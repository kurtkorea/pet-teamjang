"""검수된 강아지 데이터로 YOLO11n을 RTX 5070에서 학습합니다."""

from __future__ import annotations

import sys
from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.dataset import autolabel_pairs, list_images, prepare_dataset, resolve_model
from dog_detect.gpu import assert_trainable


def _split_counts(dataset: Path) -> tuple[int, int]:
    def count(split: str) -> int:
        return len(list_images(dataset / "images" / split))

    return count("train"), count("val")


def run_train(cfg: AppConfig, from_autolabel: bool, allow_other_gpu: bool) -> Path:
    detail = assert_trainable(allow_other_gpu)
    print(f"학습 GPU: {detail}")

    import torch

    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    if vram_gb < 10 and cfg.train.batch > 32:
        print(
            f"VRAM {vram_gb:.1f} GB입니다. train.batch {cfg.train.batch}는 "
            "부족할 수 있어 16~32를 권장합니다."
        )
    if cfg.train.workers > 0 and sys.platform == "win32":
        print("Windows에서는 train.workers를 0으로 두는 편이 안전합니다.")

    dataset = cfg.paths.reviewed / "dataset"
    data_yaml = dataset / "data.yaml"
    if from_autolabel:
        pairs = autolabel_pairs(cfg.paths.autolabel)
        data_yaml = prepare_dataset(
            pairs,
            dataset,
            cfg.train.val_ratio,
            cfg.train.seed,
            cfg.cvat.label,
        )
        print("CVAT 검수본이 아니라 자동 라벨로 학습 세트를 만들었습니다.")
    elif not data_yaml.is_file():
        raise RuntimeError(
            "검수본이 없습니다. CVAT에서 검수한 뒤 cvat-pull을 실행하세요. "
            "검수 없이 시험 학습하려면 --from-autolabel 을 붙이세요."
        )

    train_count, val_count = _split_counts(dataset)
    if train_count < 2:
        raise RuntimeError("학습 이미지가 2장 미만입니다. 영상을 더 넣거나 검수본을 확인하세요.")
    if train_count < 10:
        print(f"학습 이미지 {train_count}장, 검증 {val_count}장입니다. 검수 데이터가 늘면 정확도가 올라갑니다.")
    else:
        print(f"학습 이미지 {train_count}장, 검증 {val_count}장")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics가 없습니다. scripts/setup.ps1 을 실행하세요.") from exc

    model = YOLO(resolve_model(cfg.root, cfg.train.model))
    model.train(
        data=str(data_yaml),
        epochs=cfg.train.epochs,
        imgsz=cfg.train.imgsz,
        batch=cfg.train.batch,
        device=cfg.train.device,
        workers=cfg.train.workers,
        amp=cfg.train.amp,
        patience=cfg.train.patience,
        cache=cfg.train.cache,
        seed=cfg.train.seed,
        project=str(cfg.paths.runs),
        name="dog-yolo11n",
        exist_ok=True,
        pretrained=True,
        plots=True,
    )
    best = cfg.paths.runs / "dog-yolo11n" / "weights" / "best.pt"
    print(f"학습 가중치: {best}")
    print("다음 탐지는 config.yaml의 detect.model을 이 파일로 바꾸면 됩니다.")
    return best
