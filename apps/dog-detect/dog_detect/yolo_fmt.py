"""YOLO 라벨 한 줄, CVAT YOLO 1.1 압축, 학습 분할."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


def format_yolo_line(class_id: int, cx: float, cy: float, width: float, height: float) -> str:
    values = [min(1.0, max(0.0, float(value))) for value in (cx, cy, width, height)]
    return f"{class_id} " + " ".join(f"{value:.6f}" for value in values)


def remap_label_text(text: str, dog_index: int) -> str:
    """로컬 라벨의 클래스 0을 CVAT 라벨 순번의 dog로 바꿉니다."""
    lines: list[str] = []
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) != 5 or parts[0] != "0":
            continue
        parts[0] = str(dog_index)
        lines.append(" ".join(parts))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _unit_hash(seed: int, name: str) -> float:
    digest = hashlib.sha1(f"{seed}:{name}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def assign_split(names: list[str], val_ratio: float, seed: int) -> tuple[list[str], list[str]]:
    """파일명을 고정 시드로 train/val에 나눕니다. 이미지가 1장이면 양쪽에 넣습니다."""
    if not names:
        return [], []
    if len(names) == 1:
        return list(names), list(names)
    train: list[str] = []
    val: list[str] = []
    for name in names:
        if _unit_hash(seed, name) < val_ratio:
            val.append(name)
        else:
            train.append(name)
    if not val:
        val.append(train.pop())
    if not train:
        train.append(val.pop())
    return train, val


def write_image_zip(images: list[Path], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as archive:
        for image in images:
            archive.write(image, arcname=image.name)
    return dest


def write_yolo11_annotation_zip(
    images: list[Path],
    labels_dir: Path,
    dest: Path,
    class_names: list[str],
    dog_index: int,
) -> Path:
    """CVAT YOLO 1.1 임포트용 압축. 이미지는 태스크에 이미 올라가 있으므로 라벨만 담습니다."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    listing: list[str] = []
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("obj.names", "\n".join(class_names) + "\n")
        archive.writestr(
            "obj.data",
            f"classes = {len(class_names)}\nnames = obj.names\ntrain = train.txt\n",
        )
        for image in images:
            label_path = labels_dir / f"{image.stem}.txt"
            text = label_path.read_text(encoding="utf-8") if label_path.exists() else ""
            archive.writestr(
                f"obj_train_data/{image.stem}.txt",
                remap_label_text(text, dog_index),
            )
            listing.append(f"obj_train_data/{image.name}")
        archive.writestr("train.txt", "\n".join(listing) + ("\n" if listing else ""))
    return dest
