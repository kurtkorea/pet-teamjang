"""F:\\dog_db\\detect 이미지 + detect_log.csv → YOLO 자동 라벨."""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.yolo_fmt import format_yolo_line


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _maix_root(cfg: AppConfig) -> Path:
    raw = getattr(cfg, "_maix_root", None)
    if raw is not None:
        return Path(raw)
    # config.yaml paths.maix_root (load_config에는 없음 → yaml 직접)
    import yaml

    config_path = cfg.root / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    value = (data.get("paths") or {}).get("maix_root", "F:/dog_db/detect")
    path = Path(value)
    if not path.is_absolute():
        path = cfg.root / path
    return path


def _link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return "exists"
    try:
        os.link(src, dst)
        return "link"
    except OSError:
        import shutil

        shutil.copy2(src, dst)
        return "copy"


def _pixel_to_yolo(x: float, y: float, w: float, h: float, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    cx = (x + w / 2.0) / img_w
    cy = (y + h / 2.0) / img_h
    nw = w / img_w
    nh = h / img_h
    return cx, cy, nw, nh


def _image_size(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as img:
        return img.size  # (w, h)


def _index_local_images(maix_root: Path) -> dict[str, Path]:
    """ok/miss 및 날짜 하위폴더(miss/20261111 등)까지 수집."""
    mapping: dict[str, Path] = {}
    for folder in ("ok", "miss", "ok_sleep", "miss_sleep", "miss_lying"):
        directory = maix_root / folder
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.suffix.lower() in IMAGE_EXTS and path.is_file():
                mapping[path.name] = path
    return mapping


def _log_csv_paths(maix_root: Path) -> list[Path]:
    log_dir = maix_root / "log"
    paths: list[Path] = []
    root_csv = log_dir / "detect_log.csv"
    if root_csv.is_file():
        paths.append(root_csv)
    if log_dir.is_dir():
        for path in sorted(log_dir.rglob("detect_log.csv")):
            if path.resolve() != root_csv.resolve():
                paths.append(path)
    return paths


def _load_dog_boxes(log_paths: list[Path]) -> dict[str, list[tuple[float, float, float, float, float]]]:
    boxes: dict[str, list[tuple[float, float, float, float, float]]] = defaultdict(list)
    for log_path in log_paths:
        with log_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                label = (row.get("label") or "").strip().lower()
                if label != "dog":
                    continue
                remote = row.get("path") or ""
                name = Path(remote.replace("\\", "/")).name
                if not name:
                    continue
                try:
                    score = float(row.get("score") or 0)
                    x = float(row.get("x") or 0)
                    y = float(row.get("y") or 0)
                    w = float(row.get("w") or 0)
                    h = float(row.get("h") or 0)
                except ValueError:
                    continue
                if w <= 1 or h <= 1:
                    continue
                boxes[name].append((x, y, w, h, score))
    return boxes


def import_maix(cfg: AppConfig) -> None:
    maix_root = _maix_root(cfg)
    log_paths = _log_csv_paths(maix_root)
    if not log_paths:
        raise RuntimeError(f"CSV가 없습니다: {maix_root / 'log'}/**/detect_log.csv")

    images_dir = cfg.paths.autolabel / "images"
    labels_dir = cfg.paths.autolabel / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    local = _index_local_images(maix_root)
    if not local:
        raise RuntimeError(f"이미지가 없습니다: {maix_root}\\ok|miss|...")

    # filename -> list of dog boxes (pixel)
    boxes = _load_dog_boxes(log_paths)

    # 같은 파일에 박스가 여러 개면 점수 높은 것만 (저장 로직이 best 1개였음)
    best_box: dict[str, tuple[float, float, float, float, float]] = {}
    for name, items in boxes.items():
        best_box[name] = max(items, key=lambda item: item[4])

    linked = labeled = empty = missing_csv = 0
    size_cache: dict[str, tuple[int, int]] = {}

    for name, src in sorted(local.items()):
        dst = images_dir / name
        how = _link_or_copy(src, dst)
        if how in {"link", "copy"}:
            linked += 1

        label_path = labels_dir / f"{Path(name).stem}.txt"
        box = best_box.get(name)
        if box is None:
            label_path.write_text("", encoding="utf-8")
            empty += 1
            missing_csv += 1
            continue

        x, y, w, h, _score = box
        if name not in size_cache:
            size_cache[name] = _image_size(src)
        img_w, img_h = size_cache[name]
        cx, cy, nw, nh = _pixel_to_yolo(x, y, w, h, img_w, img_h)
        label_path.write_text(format_yolo_line(0, cx, cy, nw, nh) + "\n", encoding="utf-8")
        labeled += 1

    print(f"소스: {maix_root}")
    print(f"CSV: {len(log_paths)}개")
    print(f"작업: {cfg.paths.autolabel}")
    print(f"이미지: {len(local)} (신규 link/copy {linked})")
    print(f"dog 라벨: {labeled}")
    print(f"빈 라벨: {empty} (CSV에 dog 없음/cat만 등)")
    print("다음(검수): python -m maxi_dog_detect cvat-push")
    print("다음(기존 검수본+빈 miss 병합): python -m maxi_dog_detect merge-negatives")
