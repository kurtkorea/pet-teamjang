"""CVAT 태스크를 기존 reviewed/dataset 에 병합 (덮어쓰지 않음)."""

from __future__ import annotations

import shutil
from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.cvat_io import YOLO_EXPORT, _ensure_format, _export_task, connect, load_task_ids
from dog_detect.dataset import (
    dedupe_pairs,
    exported_pairs,
    list_images,
    safe_extract,
    write_data_yaml,
)
from dog_detect.yolo_fmt import assign_split

from maxi_dog_detect.import_maix import _link_or_copy


def _reviewed_names(dataset: Path) -> set[str]:
    names: set[str] = set()
    for split in ("train", "val"):
        for path in list_images(dataset / "images" / split):
            names.add(path.name)
    return names


def _find_split(dataset: Path, name: str) -> str | None:
    for split in ("train", "val"):
        if (dataset / "images" / split / name).is_file():
            return split
    return None


def merge_pull(cfg: AppConfig, task_ids: list[int] | None) -> None:
    dataset = cfg.paths.reviewed / "dataset"
    if not (dataset / "data.yaml").is_file():
        raise RuntimeError("기존 reviewed/dataset 이 없습니다. 먼저 전체 cvat-pull 이 필요합니다.")

    ids = load_task_ids(cfg, task_ids)
    raw = cfg.paths.reviewed / "raw_merge"
    if raw.exists():
        shutil.rmtree(raw)
    raw.mkdir(parents=True, exist_ok=True)

    with connect(cfg) as client:
        _ensure_format(client, "export", YOLO_EXPORT)
        for task_id in ids:
            task = client.tasks.retrieve(task_id)
            zip_path = raw / f"task_{task_id}.zip"
            print(f"검수본 다운로드: task {task_id}")
            _export_task(task, zip_path)
            safe_extract(zip_path, raw / f"task_{task_id}")

    pairs = []
    for task_id in ids:
        pairs.extend(exported_pairs(raw / f"task_{task_id}"))
    pairs = dedupe_pairs(pairs)
    if not pairs:
        raise RuntimeError("병합할 이미지가 없습니다.")

    existing = _reviewed_names(dataset)
    new_names = [src.name for src, _ in pairs if src.name not in existing]
    update_names = [src.name for src, _ in pairs if src.name in existing]
    train_new, val_new = assign_split(new_names, cfg.train.val_ratio, cfg.train.seed)
    split_of = {name: "train" for name in train_new}
    split_of.update({name: "val" for name in val_new})

    added = updated = 0
    by_name = {src.name: (src, label) for src, label in pairs}
    for name, (src, label) in by_name.items():
        split = _find_split(dataset, name) or split_of.get(name)
        if split is None:
            continue
        img_dst = dataset / "images" / split / name
        label_dst = dataset / "labels" / split / f"{Path(name).stem}.txt"
        if name in existing:
            # 라벨/이미지 갱신
            if img_dst.exists() or img_dst.is_symlink():
                img_dst.unlink()
            _link_or_copy(src, img_dst)
            label_dst.parent.mkdir(parents=True, exist_ok=True)
            if label is not None and label.is_file():
                label_dst.write_text(label.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                label_dst.write_text("", encoding="utf-8")
            updated += 1
        else:
            _link_or_copy(src, img_dst)
            label_dst.parent.mkdir(parents=True, exist_ok=True)
            if label is not None and label.is_file():
                label_dst.write_text(label.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                label_dst.write_text("", encoding="utf-8")
            added += 1

    write_data_yaml(dataset, cfg.cvat.label)
    print(f"기존: {len(existing)}")
    print(f"신규 추가: {added} (train {len(train_new)}, val {len(val_new)})")
    print(f"기존 갱신: {updated}")
    print(f"학습 데이터: {dataset / 'data.yaml'}")
    print("다음: python -m maxi_dog_detect train --allow-other-gpu")
