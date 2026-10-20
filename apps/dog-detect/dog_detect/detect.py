"""저장된 영상을 YOLO11n에 넣어 강아지 박스 라벨을 저장합니다."""

from __future__ import annotations

import json
from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.dataset import count_label_files, list_videos, resolve_model
from dog_detect.gpu import resolve_detect_device
from dog_detect.sampling import frame_stem, frame_step, should_infer
from dog_detect.yolo_fmt import format_yolo_line


def dog_class_ids(model, class_name: str) -> list[int]:
    names = model.names
    items = names.items() if isinstance(names, dict) else enumerate(names)
    ids = [int(index) for index, name in items if str(name) == class_name]
    if not ids:
        raise RuntimeError(
            f"모델에 '{class_name}' 클래스가 없습니다. COCO 가중치 yolo11n.pt 를 사용하세요."
        )
    return ids


def dog_lines(result, min_area: float) -> tuple[list[str], list[dict]]:
    lines: list[str] = []
    meta: list[dict] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return lines, meta
    for box in boxes:
        cx, cy, width, height = (float(value) for value in box.xywhn.reshape(-1).tolist()[:4])
        if width * height < min_area:
            continue
        conf = float(box.conf.reshape(-1)[0])
        lines.append(format_yolo_line(0, cx, cy, width, height))
        meta.append(
            {
                "conf": round(conf, 4),
                "xywhn": [round(cx, 6), round(cy, 6), round(width, 6), round(height, 6)],
            }
        )
    return lines, meta


def _write_jpeg(path: Path, frame, cv2, quality: int) -> None:
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError(f"이미지 저장에 실패했습니다: {path}")
    path.write_bytes(encoded.tobytes())


def _gray64(frame, cv2):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)


def _iter_sampled(video: Path, sample_fps: float, cv2):
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video}")
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        step = frame_step(fps, sample_fps)
        effective_fps = fps if fps > 0 else 30.0
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if index % step == 0:
                yield index, index / effective_fps, frame, total, step
            index += 1
    finally:
        capture.release()


def _detect_video(
    cfg: AppConfig,
    video: Path,
    model,
    dog_ids: list[int],
    device: str,
    images_dir: Path,
    labels_dir: Path,
    manifest,
    cv2,
    np,
    tqdm,
) -> int:
    settings = cfg.detect
    pending: list[tuple[str, int, float, object]] = []
    prev_small = None
    last_infer_at: float | None = None
    saved_this = 0
    newly = 0
    limit = settings.max_frames_per_video

    def flush() -> None:
        nonlocal newly, saved_this
        if not pending:
            return
        frames = [item[3] for item in pending]
        results = list(
            model.predict(
                source=frames,
                classes=dog_ids,
                conf=settings.conf,
                iou=settings.iou,
                imgsz=settings.imgsz,
                device=device,
                half=device != "cpu",
                stream=False,
                verbose=False,
            )
        )
        if len(results) != len(pending):
            raise RuntimeError("탐지 결과 수가 프레임 수와 다릅니다.")
        for item, result in zip(pending, results):
            if limit and saved_this >= limit:
                break
            stem, frame_index, timestamp, frame = item
            lines, meta = dog_lines(result, settings.min_box_area)
            if not lines and not settings.save_empty:
                continue
            image_path = images_dir / f"{stem}.jpg"
            label_path = labels_dir / f"{stem}.txt"
            _write_jpeg(image_path, frame, cv2, settings.jpeg_quality)
            label_path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")
            manifest.write(
                json.dumps(
                    {
                        "image": image_path.name,
                        "video": str(video),
                        "frame": frame_index,
                        "time_sec": round(timestamp, 3),
                        "boxes": meta,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            saved_this += 1
            newly += 1
        pending.clear()

    sampled = _iter_sampled(video, settings.sample_fps, cv2)
    first = next(sampled, None)
    if first is None:
        print("  프레임이 없습니다.")
        return 0
    _index, _ts, _frame, total, step = first
    expected = (total + step - 1) // step if total > 0 else None

    def frames():
        yield first
        yield from sampled

    iterator = frames()
    if tqdm is not None:
        iterator = tqdm(iterator, total=expected, desc=video.name, unit="frame")

    for frame_index, timestamp, frame, _total, _step in iterator:
        if limit and saved_this >= limit:
            break
        if frame is None or getattr(frame, "size", 0) == 0:
            continue
        try:
            small = _gray64(frame, cv2)
        except cv2.error:
            continue
        diff = None
        if prev_small is not None:
            diff = float(np.abs(prev_small.astype(np.int16) - small.astype(np.int16)).mean())
        stem = frame_stem(video, frame_index)
        image_path = images_dir / f"{stem}.jpg"
        if image_path.exists():
            prev_small = small
            last_infer_at = timestamp
            saved_this += 1
            continue
        elapsed = 1e9 if last_infer_at is None else timestamp - last_infer_at
        if not should_infer(elapsed, diff, settings.min_frame_diff, settings.max_gap_seconds):
            continue
        prev_small = small
        last_infer_at = timestamp
        pending.append((stem, frame_index, timestamp, frame.copy()))
        if len(pending) >= max(1, settings.batch):
            flush()
    flush()
    print(f"  신규 저장 {newly}장")
    return newly


def run_detect(cfg: AppConfig, video: Path | None) -> None:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("opencv-python이 없습니다. scripts/setup.ps1 을 실행하세요.") from exc
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics가 없습니다. scripts/setup.ps1 을 실행하세요.") from exc
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    source = video if video is not None else cfg.paths.videos
    videos = list_videos(source)
    if not videos:
        raise RuntimeError(f"영상이 없습니다: {source}")

    device = resolve_detect_device(cfg.detect.device)
    model = YOLO(resolve_model(cfg.root, cfg.detect.model))
    dog_ids = dog_class_ids(model, cfg.detect.class_name)

    images_dir = cfg.paths.autolabel / "images"
    labels_dir = cfg.paths.autolabel / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    newly = 0
    manifest_path = cfg.paths.autolabel / "manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as manifest:
        for video_path in videos:
            print(f"영상: {video_path}")
            newly += _detect_video(
                cfg,
                video_path,
                model,
                dog_ids,
                device,
                images_dir,
                labels_dir,
                manifest,
                cv2,
                np,
                tqdm,
            )

    nonempty, empty = count_label_files(labels_dir)
    print(f"이번 실행에서 저장한 프레임: {newly}")
    print(f"누적 라벨: 박스 {nonempty}, 빈 라벨 {empty}")
    print(f"출력: {images_dir}")
    if nonempty == 0 and not cfg.detect.save_empty:
        print("강아지 박스가 없습니다. detect.conf를 낮추거나 영상에 강아지가 보이는지 확인하세요.")
