"""기존 검수본(reviewed)에 강아지 없는 miss 이미지를 빈 라벨로 병합."""

from __future__ import annotations

from pathlib import Path

from dog_detect.config import AppConfig
from dog_detect.dataset import list_images, write_data_yaml
from dog_detect.yolo_fmt import assign_split

from maxi_dog_detect.import_maix import _index_local_images, _link_or_copy, _maix_root


def _reviewed_names(dataset: Path) -> set[str]:
    names: set[str] = set()
    for split in ("train", "val"):
        for path in list_images(dataset / "images" / split):
            names.add(path.name)
    return names


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def merge_negatives(
    cfg: AppConfig,
    miss_only: bool = True,
    folder: str | None = None,
) -> None:
    """maix miss(및 하위 날짜폴더) 중 reviewed에 없는 이미지를 빈 라벨로 추가.

    folder 를 주면 해당 하위폴더만 병합합니다 (예: miss/20261112-1).
    """
    dataset = cfg.paths.reviewed / "dataset"
    if not (dataset / "data.yaml").is_file():
        raise RuntimeError(
            "검수본이 없습니다. 먼저 cvat-pull 로 reviewed/dataset 을 만드세요."
        )

    maix_root = _maix_root(cfg)
    if folder:
        src_dir = Path(folder)
        if not src_dir.is_absolute():
            src_dir = maix_root / folder
        if not src_dir.is_dir():
            raise RuntimeError(f"폴더 없음: {src_dir}")
        local = {
            p.name: p
            for p in sorted(src_dir.iterdir())
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        }
        source_desc = str(src_dir)
    else:
        local = _index_local_images(maix_root)
        if miss_only:
            local = {
                name: path
                for name, path in local.items()
                if "miss" in path.parts
            }
        source_desc = str(maix_root)

    existing = _reviewed_names(dataset)
    candidates = sorted(name for name in local if name not in existing)
    if not candidates:
        print("추가할 신규 miss 이미지가 없습니다.")
        print(f"reviewed 기존: {len(existing)}")
        return

    train_names, val_names = assign_split(
        candidates, cfg.train.val_ratio, cfg.train.seed
    )
    added = {"train": 0, "val": 0}
    for split, names in (("train", train_names), ("val", val_names)):
        for name in names:
            src = local[name]
            img_dst = dataset / "images" / split / name
            label_dst = dataset / "labels" / split / f"{Path(name).stem}.txt"
            _link_or_copy(src, img_dst)
            label_dst.parent.mkdir(parents=True, exist_ok=True)
            label_dst.write_text("", encoding="utf-8")
            added[split] += 1

    write_data_yaml(dataset, cfg.cvat.label)
    print(f"소스: {source_desc}")
    print(f"병합 대상: {dataset}")
    print(f"기존 reviewed: {len(existing)}")
    print(f"신규 hard-neg(빈 라벨): {len(candidates)} (train {added['train']}, val {added['val']})")
    print("다음: python -m maxi_dog_detect train --finetune --allow-other-gpu")
