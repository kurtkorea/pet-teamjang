import os
import json
import time
import threading
import subprocess
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Any, Literal

import cv2
import numpy as np
import psycopg
import requests
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="PET AI Worker", version="0.2.0")
DATABASE_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
MODEL_PATH = os.getenv("MODEL_PATH", "yolo11n-pose.pt")
DOG_MODEL_PATH = os.getenv("DOG_MODEL_PATH", "yolo11n.pt")
DEVICE = os.getenv("DEVICE", "auto")
RTSP_URL = os.getenv("RTSP_URL", "")
model = None
dog_model = None
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
live_thread: threading.Thread | None = None
live_stop = threading.Event()
live_lock = threading.Lock()
live_running = False
auto_track = {"enabled": False, "dead_zone": 0.18, "sensitivity": 1.0, "speed": 0.35, "invert_pan": True, "invert_tilt": False}
inference_config = {"imgsz": 896, "conf": 0.02, "iou": 0.80, "max_det": 20}
dog_inference_config = {"imgsz": 768, "conf": 0.10, "iou": 0.75, "max_det": 10}
latest_jpeg: bytes | None = None
frame_condition = threading.Condition()

def resolve_device() -> str:
    if DEVICE == "auto":
        import torch
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if DEVICE.startswith("cuda"):
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA device requested but CUDA is unavailable")
    return DEVICE

def ptz_move(direction: str) -> None:
    from onvif import ONVIFCamera
    parsed = urlparse(RTSP_URL)
    if not parsed.hostname or not parsed.username or not parsed.password:
        raise RuntimeError("RTSP_URL credentials are required for ONVIF PTZ")
    camera = ONVIFCamera(parsed.hostname, 2020, parsed.username, parsed.password)
    media = camera.create_media_service()
    ptz = camera.create_ptz_service()
    profile = media.GetProfiles()[0]
    vectors = {"left": (0.5, 0), "right": (-0.5, 0), "up": (0, 0.5), "down": (0, -0.5)}
    if direction == "home":
        ptz.GotoHomePosition({"ProfileToken": profile.token})
        return
    if direction not in vectors:
        raise ValueError("direction must be left, right, up, down, or home")
    x, y = vectors[direction]
    if auto_track["invert_pan"]: x = -x
    if auto_track["invert_tilt"]: y = -y
    distance = 0.15 * auto_track["speed"]
    ptz.RelativeMove({
        "ProfileToken": profile.token,
        "Translation": {"PanTilt": {"x": x * distance, "y": y * distance}},
        "Speed": {"PanTilt": {"x": auto_track["speed"], "y": auto_track["speed"]}}
    })

class InferenceRequest(BaseModel):
    camera_id: str
    frame_path: str
    sample_every: int = 5

class PTZRequest(BaseModel):
    direction: str

class AutoTrackRequest(BaseModel):
    enabled: bool
    dead_zone: float = 0.18
    sensitivity: float = 1.0
    speed: float = 0.35
    invert_pan: bool = True
    invert_tilt: bool = False

class InferenceConfigRequest(BaseModel):
    target: Literal["human", "dog"] = "human"
    imgsz: int = 768
    conf: float = 0.05
    iou: float = 0.80
    max_det: int = 20

def clamp_inference_config(request: InferenceConfigRequest) -> dict[str, Any]:
    return {
        "imgsz": max(320, min(request.imgsz, 1280)),
        "conf": max(0.01, min(request.conf, 0.9)),
        "iou": max(0.1, min(request.iou, 0.95)),
        "max_det": max(1, min(request.max_det, 50)),
    }

def ensure_schema() -> None:
    if not DATABASE_URL:
        return
    statement = "CREATE TABLE IF NOT EXISTS pet_events (id BIGSERIAL PRIMARY KEY, camera_id TEXT NOT NULL, dog_id TEXT, event_type TEXT NOT NULL, behavior TEXT, confidence REAL, frame_number INTEGER, bbox JSONB, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, occurred_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    for attempt in range(1, 31):
        try:
            with psycopg.connect(DATABASE_URL) as connection:
                connection.execute(statement)
                connection.commit()
            return
        except psycopg.OperationalError:
            if attempt == 30:
                raise
            time.sleep(2)

def get_model():
    global model
    if model is None:
        from ultralytics import YOLO
        model = YOLO(MODEL_PATH)
    return model


def _use_half(device: str) -> bool:
    # Ada laptop + 일부 드라이버에서 half warmup/추론이 멈추는 경우가 있어 기본은 FP32.
    return os.getenv("TORCH_HALF", "0") in {"1", "true", "TRUE", "yes"}

def get_dog_model():
    global dog_model
    if dog_model is None:
        from ultralytics import YOLO
        dog_model = YOLO(DOG_MODEL_PATH)
    return dog_model


def dog_class_ids(detector) -> list[int]:
    """COCO dog=16, dog-detect 미세조정은 보통 class 0=dog."""
    names = getattr(detector, "names", None) or {}
    items = names.items() if isinstance(names, dict) else enumerate(names)
    ids = [int(i) for i, name in items if str(name).lower() == "dog"]
    if ids:
        return ids
    if len(names) == 1:
        return [0]
    return [16]

def behavior_for(track_id: int, center: tuple[float, float], previous: dict[int, tuple[float, float]], box: list[float] | None = None) -> str:
    old = previous.get(track_id)
    previous[track_id] = center
    if old is None:
        return "standing"
    distance = ((center[0] - old[0]) ** 2 + (center[1] - old[1]) ** 2) ** 0.5
    if distance >= 25:
        return "running"
    if distance >= 8:
        return "walking"
    if box is not None:
        width = max(1.0, box[2] - box[0])
        height = max(1.0, box[3] - box[1])
        ratio = width / height
        if ratio >= 1.55:
            return "lying"
        if ratio <= 0.78:
            return "sitting"
    return "resting"

def suppress_overlapping_boxes(items: list[tuple[int, list[float], float]], iou_threshold: float = 0.55) -> list[tuple[int, list[float], float]]:
    kept: list[tuple[int, list[float], float]] = []
    for candidate in sorted(items, key=lambda item: item[2], reverse=True):
        _, box, _ = candidate
        area = max(1.0, (box[2] - box[0]) * (box[3] - box[1]))
        duplicate = False
        for _, other, _ in kept:
            ix1, iy1 = max(box[0], other[0]), max(box[1], other[1])
            ix2, iy2 = min(box[2], other[2]), min(box[3], other[3])
            intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
            other_area = max(1.0, (other[2] - other[0]) * (other[3] - other[1]))
            if intersection / max(1.0, area + other_area - intersection) >= iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    return kept

def save_events(events: list[dict[str, Any]]) -> None:
    if not DATABASE_URL or not events:
        return
    db_events = [{**event, "bbox": json.dumps(event["bbox"]), "metadata": "{}"} for event in events]
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.executemany("INSERT INTO pet_events (camera_id, dog_id, event_type, behavior, confidence, frame_number, bbox, metadata) VALUES (%(camera_id)s, %(dog_id)s, %(event_type)s, %(behavior)s, %(confidence)s, %(frame_number)s, %(bbox)s::jsonb, %(metadata)s::jsonb)", db_events)
        connection.commit()

def run_detection(request: InferenceRequest) -> dict[str, Any]:
    dog_detector = get_dog_model()
    device = resolve_device()
    capture = cv2.VideoCapture(request.frame_path)
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {request.frame_path}")
    detections: list[dict[str, Any]] = []
    behaviors: list[dict[str, Any]] = []
    previous: dict[int, tuple[float, float]] = {}
    frame_number = 0
    dog_classes = dog_class_ids(dog_detector)
    for result in dog_detector.track(
        source=request.frame_path,
        stream=True,
        persist=True,
        tracker="bytetrack.yaml",
        classes=dog_classes,
        device=device,
        **dog_inference_config,
        half=_use_half(device),
        verbose=False,
    ):
        frame_number += 1
        if frame_number % max(request.sample_every, 1) != 0:
            continue
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            continue
        ids = boxes.id.int().cpu().tolist() if boxes.id is not None else list(range(len(boxes)))
        for track_id, box, confidence in zip(ids, boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist()):
            x1, y1, x2, y2 = box
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            behavior = behavior_for(track_id, center, previous)
            event = {"camera_id": request.camera_id, "dog_id": f"dog_{track_id:02d}", "event_type": "dog.detected", "behavior": behavior, "confidence": float(confidence), "frame_number": frame_number, "bbox": box, "metadata": "{}"}
            detections.append({**event, "track_id": track_id})
            behaviors.append({"dog_id": event["dog_id"], "behavior": behavior, "frame_number": frame_number})
    capture.release()
    save_events(detections)
    try:
        requests.post(f"{os.getenv('API_URL', 'http://api:3000')}/internal/detections", json={"camera_id": request.camera_id, "detections": detections, "behaviors": behaviors}, timeout=2)
    except requests.RequestException:
        pass
    return {"detections": detections, "behaviors": behaviors, "frames_analyzed": frame_number, "device": device, "dog_classes": dog_classes, "dog_model": DOG_MODEL_PATH}

def live_detection_loop(camera_id: str) -> None:
    global live_running, latest_jpeg
    detector = get_model()
    dog_detector = get_dog_model()
    device = resolve_device()
    dog_classes = dog_class_ids(dog_detector)
    print(f"live: dog_model={DOG_MODEL_PATH} dog_classes={dog_classes} names={getattr(dog_detector, 'names', {})}", flush=True)
    previous: dict[int, tuple[float, float]] = {}
    while not live_stop.is_set():
        width, height = 960, 540
        print("live: opening RTSP stream with OpenCV", flush=True)
        capture = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        capture.set(cv2.CAP_PROP_FPS, 15)
        if not capture.isOpened():
            print("live: OpenCV could not open RTSP stream", flush=True)
            capture.release()
            time.sleep(1)
            continue
        capture_stop = threading.Event()
        capture_lock = threading.Lock()
        latest_source: list[np.ndarray | None] = [None]

        def capture_loop() -> None:
            while not capture_stop.is_set():
                ok, source = capture.read()
                if ok and source is not None:
                    with capture_lock:
                        latest_source[0] = source

        capture_thread = threading.Thread(target=capture_loop, daemon=True)
        capture_thread.start()
        frame_number = 0
        last_publish = 0.0
        last_db_save = 0.0
        last_inference = 0.0
        last_dog_detections: list[dict[str, Any]] = []
        dog_missing_frames = 0
        while not live_stop.is_set():
            with capture_lock:
                source_frame = latest_source[0]
            if source_frame is None:
                time.sleep(0.01)
                continue
            frame = cv2.resize(source_frame, (width, height), interpolation=cv2.INTER_AREA)
            if frame_number == 0:
                print("live: first frame received", flush=True)
            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                with frame_condition:
                    latest_jpeg = encoded.tobytes()
                    frame_condition.notify_all()
            now = time.monotonic()
            if now - last_inference < (1 / 3):
                time.sleep(0.005)
                continue
            last_inference = now
            frame_number += 1
            human_result = detector.track(source=frame, persist=True, tracker="bytetrack.yaml", classes=[0], device=device, **inference_config, half=_use_half(device), verbose=False)[0]
            dog_result = dog_detector.track(source=frame, persist=True, tracker="bytetrack.yaml", classes=dog_classes, device=device, **dog_inference_config, half=_use_half(device), verbose=False)[0]
            detections: list[dict[str, Any]] = []
            boxes = human_result.boxes
            raw_class_ids: list[int] = []
            if boxes is not None and len(boxes) > 0:
                ids = boxes.id.int().cpu().tolist() if boxes.id is not None else list(range(len(boxes)))
                class_ids = boxes.cls.int().cpu().tolist() if boxes.cls is not None else [-1] * len(boxes)
                raw_class_ids = class_ids
                human_items = suppress_overlapping_boxes(list(zip(ids, boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist())))
                for track_id, box, confidence in human_items:
                    class_id = 0
                    x1, y1, x2, y2 = box
                    behavior = behavior_for(track_id, ((x1 + x2) / 2, (y1 + y2) / 2), previous, box)
                    label = "human" if class_id == 0 else "dog"
                    detections.append({"camera_id": camera_id, "dog_id": f"{label}_{track_id:02d}", "label": label, "event_type": f"{label}.detected", "behavior": behavior, "confidence": float(confidence), "frame_number": frame_number, "bbox": box, "track_id": track_id, "metadata": "{}"})
            dog_boxes = dog_result.boxes
            if dog_boxes is not None and len(dog_boxes) > 0:
                dog_missing_frames = 0
                dog_ids = dog_boxes.id.int().cpu().tolist() if dog_boxes.id is not None else list(range(len(dog_boxes)))
                for track_id, box, confidence in zip(dog_ids, dog_boxes.xyxy.cpu().tolist(), dog_boxes.conf.cpu().tolist()):
                    x1, y1, x2, y2 = box
                    behavior = behavior_for(1000 + track_id, ((x1 + x2) / 2, (y1 + y2) / 2), previous, box)
                    detections.append({"camera_id": camera_id, "dog_id": f"dog_{track_id:02d}", "label": "dog", "event_type": "dog.detected", "behavior": behavior, "confidence": float(confidence), "frame_number": frame_number, "bbox": box, "track_id": 1000 + track_id, "metadata": "{}"})
                last_dog_detections = [item.copy() for item in detections if item.get("label") == "dog"]
            elif last_dog_detections and dog_missing_frames < 3:
                dog_missing_frames += 1
                detections.extend(item | {"frame_number": frame_number, "metadata": '{"smoothed":true}'} for item in last_dog_detections)
            else:
                dog_missing_frames = 0
            if frame_number % 30 == 0:
                raw_count = (len(boxes) if boxes is not None else 0) + (len(dog_boxes) if dog_boxes is not None else 0)
                dog_conf = dog_boxes.conf.cpu().tolist() if dog_boxes is not None and len(dog_boxes) > 0 else []
                print(f"live: frame={frame_number} raw={raw_count} humans={len(boxes) if boxes is not None else 0} dogs={len(dog_boxes) if dog_boxes is not None else 0} dog_conf={dog_conf} device={device}", flush=True)
            if auto_track["enabled"] and detections:
                target = max(detections, key=lambda d: (d["bbox"][2] - d["bbox"][0]) * (d["bbox"][3] - d["bbox"][1]))
                x1, y1, x2, y2 = target["bbox"]
                cx, cy = ((x1 + x2) / 2) / width, ((y1 + y2) / 2) / height
                dz = auto_track["dead_zone"] / 2
                direction = "left" if cx < 0.5 - dz else "right" if cx > 0.5 + dz else "up" if cy < 0.5 - dz else "down" if cy > 0.5 + dz else None
                if direction:
                    try: ptz_move(direction)
                    except Exception as error: print(f"auto-track PTZ error: {error}", flush=True)
            payload = {"camera_id": camera_id, "detections": detections, "behaviors": [{"dog_id": d["dog_id"], "behavior": d["behavior"], "frame_number": frame_number} for d in detections], "device": device, "live": True, "source_width": width, "source_height": height, "auto_track": auto_track}
            now = time.monotonic()
            if now - last_publish >= 0.4:
                last_publish = now
                if now - last_db_save >= 2.0:
                    last_db_save = now
                    threading.Thread(target=save_events, args=(detections.copy(),), daemon=True).start()
                try:
                    redis_client.publish("pet:detections", json.dumps(payload))
                except redis.RedisError:
                    pass
        capture_stop.set()
        capture_thread.join(timeout=2)
        capture.release()
        if not live_stop.is_set():
            time.sleep(1)
    with live_lock:
        live_running = False

@app.post("/live/start")
def live_start() -> dict[str, str]:
    global live_thread, live_running
    if not RTSP_URL:
        raise HTTPException(status_code=503, detail="RTSP_URL is not configured")
    with live_lock:
        if live_running and live_thread and live_thread.is_alive():
            return {"status": "already_running", "device": resolve_device()}
        if live_thread and live_thread.is_alive():
            live_stop.set()
            live_thread.join(timeout=5)
        live_stop.clear()
        live_running = True
        live_thread = threading.Thread(target=live_detection_loop, args=("tc70-01",), daemon=True)
        live_thread.start()
    return {"status": "started", "device": resolve_device()}

@app.post("/live/stop")
def live_stop_endpoint() -> dict[str, str]:
    global live_running
    live_stop.set()
    thread = live_thread
    if thread and thread.is_alive():
        thread.join(timeout=5)
    with live_lock:
        if not (live_thread and live_thread.is_alive()):
            live_running = False
    return {"status": "stopped"}

def mjpeg_stream():
    global latest_jpeg
    while True:
        with frame_condition:
            frame_condition.wait(timeout=2)
            jpeg = latest_jpeg
        if jpeg:
            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n"

@app.get("/stream")
def stream():
    if not live_running:
        live_start()
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/ptz/move")
def move_ptz(request: PTZRequest) -> dict[str, str]:
    try:
        ptz_move(request.direction)
        return {"status": "ok", "direction": request.direction}
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

@app.post("/ptz/auto-track")
def configure_auto_track(request: AutoTrackRequest) -> dict[str, Any]:
    auto_track.update({"enabled": request.enabled, "dead_zone": max(0.05, min(request.dead_zone, 0.6)), "sensitivity": max(0.1, min(request.sensitivity, 3.0)), "speed": max(0.1, min(request.speed, 1.0)), "invert_pan": request.invert_pan, "invert_tilt": request.invert_tilt})
    return auto_track

@app.post("/config/inference")
def configure_inference(request: InferenceConfigRequest) -> dict[str, Any]:
    clamped = clamp_inference_config(request)
    if request.target == "dog":
        dog_inference_config.update(clamped)
    else:
        inference_config.update(clamped)
    return {"human": inference_config, "dog": dog_inference_config}

@app.get("/config/inference")
def get_inference_config() -> dict[str, Any]:
    return {"human": inference_config, "dog": dog_inference_config}

@app.on_event("startup")
def startup() -> None:
    ensure_schema()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-worker", "device": DEVICE}

@app.post("/infer")
def infer(request: InferenceRequest) -> dict[str, Any]:
    try:
        result = run_detection(request)
        return {"camera_id": request.camera_id, "timestamp": datetime.now(timezone.utc).isoformat(), **result, "model_status": "yolo-bytetrack"}
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
