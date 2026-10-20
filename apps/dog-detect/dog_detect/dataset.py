"""검수본·자동 라벨을 Ultralytics 학습 폴더로 맞춥니다."""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from dog_detect.yolo_fmt import assign_split

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def list_images(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def list_videos(path: Path) -> list[Path]:
    suffixes = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
    if path.is_file():
        if path.suffix.lower() not in suffixes:
            raise RuntimeError(f"지원하지 않는 영상 형식입니다: {path.suffix}")
        return [path]
    if not path.exists():
        return []
    return sorted(item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in suffixes)


def write_data_yaml(root: Path, class_name: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "data.yaml"
    path.write_text(
        f"path: {root.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        f"  0: {class_name}\n",
        encoding="utf-8",
    )
    return path


def _place(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def resolve_model(root: Path, model: str) -> str:
    """로컬 파일이면 그 경로를, 아니면 Ultralytics가 받는 가중치 이름을 돌려줍니다."""
    path = Path(model)
    if path.is_file():
        return str(path)
    candidate = root / model
    if candidate.is_file():
        return str(candidate)
    return model


def zip_target(dest: Path, name: str) -> Path:
    pure = Path(name.replace("\\", "/"))
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise RuntimeError(f"압축 경로가 안전하지 않습니다: {name}")
    root = dest.resolve()
    target = (dest / pure).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"압축 경로가 안전하지 않습니다: {name}") from exc
    return target


def safe_extract(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if not info.filename or info.filename.endswith("/"):
                target = zip_target(dest, info.filename.rstrip("/")) if info.filename else dest
                if info.filename:
                    target.mkdir(parents=True, exist_ok=True)
                continue
            target = zip_target(dest, info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)


def find_label(image: Path) -> Path | None:
    sibling = image.with_suffix(".txt")
    if sibling.is_file():
        return sibling
    parts = list(image.parts)
    if "images" not in parts:
        return None
    index = parts.index("images")
    candidate = Path(*parts[:index], "labels", *parts[index + 1 :]).with_suffix(".txt")
    if candidate.is_file():
        return candidate
    return None


def autolabel_pairs(autolabel: Path) -> list[tuple[Path, Path | None]]:
    labels = autolabel / "labels"
    return [(image, labels / f"{image.stem}.txt") for image in list_images(autolabel / "images")]


def exported_pairs(root: Path) -> list[tuple[Path, Path | None]]:
    images = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
    return [(image, find_label(image)) for image in images]


def dedupe_pairs(pairs: list[tuple[Path, Path | None]]) -> list[tuple[Path, Path | None]]:
    chosen: dict[str, tuple[Path, Path | None]] = {}
    for image, label in pairs:
        current = chosen.get(image.name)
        if current is None:
            chosen[image.name] = (image, label)
            continue
        _, current_label = current
        current_has = current_label is not None and current_label.is_file() and current_label.stat().st_size > 0
        new_has = label is not None and label.is_file() and label.stat().st_size > 0
        if new_has and not current_has:
            chosen[image.name] = (image, label)
    return list(chosen.values())


def prepare_dataset(
    pairs: list[tuple[Path, Path | None]],
    dest: Path,
    val_ratio: float,
    seed: int,
    class_name: str,
) -> Path:
    if not pairs:
        raise RuntimeError("학습으로 넘길 이미지가 없습니다.")
    dest_resolved = dest.resolve()
    for src, _label in pairs:
        src_resolved = src.resolve()
        if src_resolved == dest_resolved or dest_resolved in src_resolved.parents:
            raise RuntimeError("출력 폴더가 원본 이미지 안에 있습니다.")
        if src_resolved.is_relative_to(dest_resolved):
            raise RuntimeError("출력 폴더가 원본과 겹칩니다.")
    names = [src.name for src, _label in pairs]
    if len(set(names)) != len(names):
        raise RuntimeError("이미지 파일명이 중복됩니다. 자동 라벨을 다시 만드세요.")
    if dest.exists():
        shutil.rmtree(dest)

    by_name = {src.name: (src, label) for src, label in pairs}
    train_names, val_names = assign_split(names, val_ratio, seed)
    for split, split_names in (("train", train_names), ("val", val_names)):
        for name in split_names:
            src, label = by_name[name]
            _place(src, dest / "images" / split / name)
            label_dest = dest / "labels" / split / f"{Path(name).stem}.txt"
            label_dest.parent.mkdir(parents=True, exist_ok=True)
            if label is not None and label.is_file():
                label_dest.write_text(label.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                label_dest.write_text("", encoding="utf-8")
    return write_data_yaml(dest, class_name)


def count_label_files(labels_dir: Path) -> tuple[int, int]:
    """(박스 있는 파일 수, 빈 파일 수)"""
    if not labels_dir.is_dir():
        return 0, 0
    nonempty = 0
    empty = 0
    for path in labels_dir.glob("*.txt"):
        if path.read_text(encoding="utf-8").strip():
            nonempty += 1
        else:
            empty += 1
    return nonempty, empty
