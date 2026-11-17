"""강아지 없는 프레임(CSV none/cat만 + 빈 라벨)을 autolabel에서 분리합니다."""

from __future__ import annotations

import csv
import shutil
from collections import defaultdict
from pathlib import Path

from dog_detect.config import AppConfig

from maxi_dog_detect.import_maix import IMAGE_EXTS, _maix_root


def _labels_by_filename(log_path: Path) -> dict[str, set[str]]:
    by_name: dict[str, set[str]] = defaultdict(set)
    with log_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name = Path((row.get("path") or "").replace("\\", "/")).name
            if not name:
                continue
            label = (row.get("label") or "").strip().lower()
            if label:
                by_name[name].add(label)
    return by_name


def _move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        src.rename(dst)
    except OSError:
        shutil.move(str(src), str(dst))


def discard_empty(cfg: AppConfig, include_cat: bool = True) -> None:
    maix_root = _maix_root(cfg)
    log_path = maix_root / "log" / "detect_log.csv"
    if not log_path.is_file():
        raise RuntimeError(f"CSV가 없습니다: {log_path}")

    images_dir = cfg.paths.autolabel / "images"
    labels_dir = cfg.paths.autolabel / "labels"
    out_root = cfg.paths.autolabel / "discarded"
    out_images = out_root / "images"
    out_labels = out_root / "labels"
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels.mkdir(parents=True, exist_ok=True)

    by_name = _labels_by_filename(log_path)
    moved = kept_dog = kept_has_box = skipped = 0
    reasons = defaultdict(int)

    for image in sorted(images_dir.iterdir()):
        if image.suffix.lower() not in IMAGE_EXTS or not image.is_file():
            continue
        label_path = labels_dir / f"{image.stem}.txt"
        has_box = label_path.is_file() and bool(label_path.read_text(encoding="utf-8").strip())
        if has_box:
            kept_has_box += 1
            continue

        csv_labels = by_name.get(image.name, set())
        if "dog" in csv_labels:
            kept_dog += 1
            continue

        if csv_labels <= {"none"} or csv_labels == set() or csv_labels <= {""}:
            reason = "none"
        elif include_cat and "cat" in csv_labels and "dog" not in csv_labels:
            reason = "cat_only"
        else:
            skipped += 1
            continue

        _move(image, out_images / image.name)
        if label_path.is_file():
            _move(label_path, out_labels / label_path.name)
        else:
            (out_labels / label_path.name).write_text("", encoding="utf-8")
        moved += 1
        reasons[reason] += 1

    print(f"폐기(이동): {moved} → {out_root}")
    for key, value in sorted(reasons.items()):
        print(f"  - {key}: {value}")
    print(f"유지(박스 있음): {kept_has_box}")
    print(f"유지(CSV dog, 박스 없음): {kept_dog}")
    print(f"건너뜀: {skipped}")
    remain = sum(1 for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    print(f"autolabel 남은 이미지: {remain}")
