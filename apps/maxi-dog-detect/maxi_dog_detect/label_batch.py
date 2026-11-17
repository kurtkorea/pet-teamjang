"""특정 miss 하위폴더만 import → YOLO 자동라벨 → CVAT 업로드."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.cvat_io import (
    YOLO_IMPORT,
    _chunks,
    _ensure_format,
    _ensure_project,
    _resource_type,
    _write_state,
    connect,
)
from dog_detect.dataset import resolve_model
from dog_detect.detect import dog_class_ids, dog_lines
from dog_detect.gpu import resolve_detect_device
from dog_detect.yolo_fmt import write_image_zip, write_yolo11_annotation_zip

from maxi_dog_detect.import_maix import _link_or_copy, _maix_root

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def label_batch(
    cfg: AppConfig,
    folder: str,
    *,
    conf: float | None = None,
    model_path: str | None = None,
) -> None:
    maix_root = _maix_root(cfg)
    src_dir = Path(folder)
    if not src_dir.is_absolute():
        src_dir = maix_root / folder
    if not src_dir.is_dir():
        raise RuntimeError(f"폴더 없음: {src_dir}")

    images = sorted(
        p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    if not images:
        raise RuntimeError(f"이미지 없음: {src_dir}")

    images_dir = cfg.paths.autolabel / "images"
    labels_dir = cfg.paths.autolabel / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    linked = 0
    for src in images:
        how = _link_or_copy(src, images_dir / src.name)
        if how in {"link", "copy"}:
            linked += 1
        label_path = labels_dir / f"{src.stem}.txt"
        if not label_path.exists():
            label_path.write_text("", encoding="utf-8")

    print(f"폴더: {src_dir}")
    print(f"이미지: {len(images)} (신규 {linked})")

    from ultralytics import YOLO

    weights = model_path or str(cfg.root / "runs" / "dog-yolo11n" / "weights" / "best.pt")
    if not Path(weights).is_file():
        weights = resolve_model(cfg.root, cfg.detect.model)
    device = resolve_detect_device(cfg.detect.device)
    conf_th = float(conf if conf is not None else min(cfg.detect.conf, 0.15))
    model = YOLO(weights)
    dog_ids = dog_class_ids(model, cfg.detect.class_name)
    print(f"모델: {weights}")
    print(f"device={device} conf={conf_th}")

    filled = multi = 0
    batch = max(1, int(cfg.detect.batch))
    for i in range(0, len(images), batch):
        chunk = images[i : i + batch]
        paths = [str(images_dir / img.name) for img in chunk]
        results = model.predict(
            source=paths,
            classes=dog_ids,
            conf=conf_th,
            iou=cfg.detect.iou,
            imgsz=cfg.detect.imgsz,
            device=device,
            verbose=False,
        )
        for img, result in zip(chunk, results):
            lines, _meta = dog_lines(result, cfg.detect.min_box_area)
            (labels_dir / f"{img.stem}.txt").write_text(
                "\n".join(lines) + ("\n" if lines else ""),
                encoding="utf-8",
            )
            if lines:
                filled += 1
            if len(lines) > 1:
                multi += 1
            print(f"  {img.name}: {len(lines)} box")

    print(f"박스 있음: {filled}/{len(images)}, 다견: {multi}")

    # CVAT: 이 배치만 업로드
    staging = cfg.paths.autolabel / "_cvat"
    staging.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = src_dir.name.replace(" ", "_")
    task_name = f"maxi-{tag}-{stamp}"
    image_paths = [images_dir / img.name for img in images]
    image_zip = staging / f"{task_name}-images.zip"
    anno_zip = staging / f"{task_name}-labels.zip"
    write_image_zip(image_paths, image_zip)
    resource_type = _resource_type()

    with connect(cfg) as client:
        project, names = _ensure_project(client, cfg)
        dog_index = names.index(cfg.cvat.label)
        _ensure_format(client, "import", YOLO_IMPORT)
        write_yolo11_annotation_zip(image_paths, labels_dir, anno_zip, names, dog_index)
        print(f"업로드: {task_name} ({len(image_paths)}장)")
        task = client.tasks.create_from_data(
            spec={"name": task_name, "project_id": project.id},
            resource_type=resource_type.LOCAL,
            resources=[str(image_zip)],
        )
        task.import_annotations(YOLO_IMPORT, str(anno_zip))
        url = f"{cfg.cvat.host}/tasks/{task.id}"
        state = {
            "created_at": stamp,
            "project_id": project.id,
            "project_name": cfg.cvat.project_name,
            "label": cfg.cvat.label,
            "tasks": [
                {"id": task.id, "name": task_name, "url": url, "images": len(image_paths)}
            ],
        }
        _write_state(cfg, state)
        print(f"검수: {url}")

    image_zip.unlink(missing_ok=True)
    anno_zip.unlink(missing_ok=True)
    shutil.rmtree(staging, ignore_errors=True)
    print("CVAT에서 사람+개 겹침 박스를 고친 뒤:")
    print(f"  python -m maxi_dog_detect cvat-pull --task-id {state['tasks'][0]['id']}")
    print("  python -m maxi_dog_detect merge-negatives  # 필요시")
    print("  python -m maxi_dog_detect train --allow-other-gpu")
