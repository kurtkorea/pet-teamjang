"""학습한 가중치로 RTSP CCTV를 실시간 탐지합니다."""

from __future__ import annotations

import os
import time
from urllib.parse import urlsplit, urlunsplit

from dog_detect.config import AppConfig
from dog_detect.dataset import resolve_model
from dog_detect.detect import dog_class_ids
from dog_detect.gpu import resolve_detect_device


def _display_source(source: str) -> str:
    parsed = urlsplit(source)
    if not parsed.username and not parsed.password:
        return source
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    user = parsed.username or ""
    netloc = f"{user}:***@{host}" if user else f"***@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def _open_capture(source: str, cv2):
    if source.startswith("rtsp://"):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
        capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    else:
        capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        capture.release()
        hint = ""
        if source.startswith("rtsp://"):
            hint = " RTSP 401이면 카메라 계정(아이디:비밀번호)을 주소에 넣으세요. 예: rtsp://user:pass@host/stream1"
        raise RuntimeError(f"영상을 열 수 없습니다: {_display_source(source)}.{hint}")
    return capture


def run_live(cfg: AppConfig, source: str | None) -> None:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python이 없습니다. scripts/setup.ps1 을 실행하세요.") from exc
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics가 없습니다. scripts/setup.ps1 을 실행하세요.") from exc

    url = (source or os.environ.get("RTSP_URL") or cfg.live.source).strip()
    if not url:
        raise RuntimeError("실시간 소스 주소가 없습니다. --source 또는 config.yaml의 live.source를 지정하세요.")

    device = resolve_detect_device(cfg.detect.device)
    model_path = resolve_model(cfg.root, cfg.detect.model)
    model = YOLO(model_path)
    dog_ids = dog_class_ids(model, cfg.detect.class_name)
    settings = cfg.detect

    print(f"소스: {_display_source(url)}", flush=True)
    print(f"모델: {model_path}", flush=True)
    print(f"장치: {device}", flush=True)
    print("창에서 q 를 누르면 종료합니다.", flush=True)

    window = "dog-detect live"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    capture = _open_capture(url, cv2)
    frame_number = 0
    last_log = 0.0
    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None or getattr(frame, "size", 0) == 0:
                print("스트림이 끊겼습니다. 다시 연결합니다.", flush=True)
                capture.release()
                time.sleep(1)
                try:
                    capture = _open_capture(url, cv2)
                except RuntimeError as exc:
                    print(exc, flush=True)
                    time.sleep(2)
                    capture = cv2.VideoCapture()
                continue

            result = model.predict(
                source=frame,
                classes=dog_ids,
                conf=settings.conf,
                iou=settings.iou,
                imgsz=settings.imgsz,
                device=device,
                verbose=False,
            )[0]
            annotated = result.plot()
            boxes = getattr(result, "boxes", None)
            count = 0 if boxes is None else len(boxes)
            cv2.putText(
                annotated,
                f"dogs={count}  q=quit",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window, annotated)
            frame_number += 1
            now = time.monotonic()
            if now - last_log >= 5:
                last_log = now
                print(f"live: frame={frame_number} dogs={count}", flush=True)
            key = cv2.waitKey(1) & 0xFF
            if key in {ord("q"), 27}:
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
        print(f"종료. 처리한 프레임: {frame_number}", flush=True)
