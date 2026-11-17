"""Smoke: one tiny train step to see if CUDA forward works."""
from ultralytics import YOLO

model = YOLO(r"runs/dog-yolo11n/weights/best.pt")
print("loaded")
model.train(
    data=r"data/reviewed/dataset/data.yaml",
    epochs=1,
    imgsz=640,
    batch=4,
    device=0,
    workers=0,
    amp=False,
    project=r"runs",
    name="smoke-train",
    exist_ok=True,
    plots=False,
    patience=1,
)
print("SMOKE_OK")
