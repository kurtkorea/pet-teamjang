"""빈/기존 YOLO 라벨에 PC YOLO11n dog 박스를 채우거나 다시 스캔합니다."""

from __future__ import annotations

from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.dataset import list_images, resolve_model
from dog_detect.detect import dog_class_ids, dog_lines
from dog_detect.gpu import resolve_detect_device


def _box_count(label_path: Path) -> int:
    if not label_path.is_file():
        return 0
    text = label_path.read_text(encoding="utf-8").strip()
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def _select_images(
    images_dir: Path,
    labels_dir: Path,
    *,
    prefix: str | None,
    empty_only: bool,
) -> list[Path]:
    selected: list[Path] = []
    for image in list_images(images_dir):
        if prefix and not image.name.lower().startswith(prefix.lower()):
            continue
        label_path = labels_dir / f"{image.stem}.txt"
        if empty_only and _box_count(label_path) > 0:
            continue
        selected.append(image)
    return selected


def autolabel_empty(
    cfg: AppConfig,
    miss_only: bool = True,
    overwrite: bool = False,
    prefix: str | None = None,
) -> None:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics가 없습니다. pip install ultralytics") from exc
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    images_dir = cfg.paths.autolabel / "images"
    labels_dir = cfg.paths.autolabel / "labels"
    if not images_dir.is_dir():
        raise RuntimeError(f"이미지 폴더가 없습니다: {images_dir} (먼저 import-maix)")

    if prefix is None and miss_only:
        prefix = "miss"

    targets = _select_images(
        images_dir,
        labels_dir,
        prefix=prefix,
        empty_only=not overwrite,
    )
    if not targets:
        print("대상 이미지가 없습니다.")
        return

    device = resolve_detect_device(cfg.detect.device)
    model = YOLO(resolve_model(cfg.root, cfg.detect.model))
    dog_ids = dog_class_ids(model, cfg.detect.class_name)
    batch = max(1, int(cfg.detect.batch))

    before_boxes = sum(_box_count(labels_dir / f"{image.stem}.txt") for image in targets)
    filled = skipped = multi_now = gained = 0
    iterator = range(0, len(targets), batch)
    if tqdm is not None:
        iterator = tqdm(iterator, desc="YOLO scan", unit="batch")

    print(
        f"대상: {len(targets)}장 "
        f"(prefix={prefix or 'ALL'}, overwrite={overwrite}, device={device}, conf={cfg.detect.conf})"
    )
    for start in iterator:
        chunk = targets[start : start + batch]
        results = list(
            model.predict(
                source=[str(path) for path in chunk],
                classes=dog_ids,
                conf=cfg.detect.conf,
                iou=cfg.detect.iou,
                imgsz=cfg.detect.imgsz,
                device=device,
                half=device != "cpu",
                stream=False,
                verbose=False,
            )
        )
        if len(results) != len(chunk):
            raise RuntimeError("탐지 결과 수가 이미지 수와 다릅니다.")
        for image, result in zip(chunk, results):
            label_path = labels_dir / f"{image.stem}.txt"
            old_count = _box_count(label_path)
            lines, _meta = dog_lines(result, cfg.detect.min_box_area)
            new_count = len(lines)
            if lines:
                label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                filled += 1
                if new_count >= 2:
                    multi_now += 1
                if new_count > old_count:
                    gained += 1
            else:
                if overwrite:
                    # 기존 박스가 있으면 유지 (전부 놓친 경우 날리지 않음)
                    if old_count > 0:
                        skipped += 1
                    else:
                        label_path.write_text("", encoding="utf-8")
                        skipped += 1
                else:
                    if not label_path.is_file():
                        label_path.write_text("", encoding="utf-8")
                    skipped += 1

    after_boxes = sum(_box_count(labels_dir / f"{image.stem}.txt") for image in targets)
    print(f"탐지 성공(≥1박스): {filled}")
    print(f"2마리 이상: {multi_now}")
    print(f"박스 수 증가한 장: {gained}")
    print(f"박스 합계: {before_boxes} → {after_boxes} (+{after_boxes - before_boxes})")
    print(f"미탐지/유지: {skipped}")
    print(f"라벨: {labels_dir}")
    print("다음: python -m maxi_dog_detect cvat-push")
