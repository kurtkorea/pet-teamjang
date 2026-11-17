"""Finetune with safer overrides after GPU hang (no mosaic/plots, small batch)."""
import time

import torch
from ultralytics import YOLO

print("warmup cuda...", flush=True)
t0 = time.time()
a = torch.randn(512, 512, device="cuda")
b = a @ a
torch.cuda.synchronize()
print(f"warmup ok {time.time() - t0:.2f}s", flush=True)

weights = r"runs/dog-yolo11n/weights/best.pt"
data = r"data/reviewed/dataset/data.yaml"
print("finetune from:", weights, flush=True)
model = YOLO(weights)
model.train(
    data=data,
    epochs=50,
    imgsz=640,
    batch=8,
    device=0,
    workers=0,
    amp=False,
    patience=30,
    cache=False,
    seed=42,
    project=r"runs",
    name="dog-yolo11n",
    exist_ok=True,
    pretrained=True,
    plots=False,
    mosaic=0.0,
    mixup=0.0,
    copy_paste=0.0,
    close_mosaic=0,
)
print("TRAIN_OK", flush=True)
