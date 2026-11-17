"""maxi-dog-detect 명령."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        type=Path,
        default=APP_ROOT / "config.yaml",
        help="config.yaml 경로",
    )

    parser = argparse.ArgumentParser(
        prog="maxi-dog-detect",
        description="MaixCAM2 Detect 이미지/CSV → CVAT 검수 → YOLO11n 학습",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser(
        "import-maix",
        parents=[common],
        help="F:/dog_db/detect 이미지+CSV로 YOLO 자동 라벨을 만듭니다.",
    )
    empty = commands.add_parser(
        "autolabel-empty",
        parents=[common],
        help="빈 라벨(기본: miss*)에 PC YOLO11n dog 박스를 채웁니다.",
    )
    empty.add_argument(
        "--all-empty",
        action="store_true",
        help="miss뿐 아니라 빈 라벨 전체도 돌립니다.",
    )
    empty.add_argument(
        "--ok",
        action="store_true",
        help="ok_* 이미지만 대상으로 합니다.",
    )
    empty.add_argument(
        "--overwrite",
        action="store_true",
        help="이미 박스가 있어도 다시 탐지합니다(다견 보완).",
    )
    discard = commands.add_parser(
        "discard-empty",
        parents=[common],
        help="강아지 없는 프레임(CSV none/cat만 + 빈 라벨)을 discarded/ 로 분리합니다.",
    )
    discard.add_argument(
        "--keep-cat",
        action="store_true",
        help="cat-only 프레임은 폐기하지 않습니다.",
    )
    commands.add_parser(
        "cvat-push",
        parents=[common],
        help="CVAT 프로젝트 maxi-dog-detect 에 업로드합니다.",
    )
    pull = commands.add_parser(
        "cvat-pull",
        parents=[common],
        help="CVAT 검수본을 학습 폴더로 내려받습니다.",
    )
    pull.add_argument("--task-id", type=int, action="append", dest="task_ids")
    pull.add_argument(
        "--merge",
        action="store_true",
        help="기존 reviewed/dataset 을 유지한 채 태스크만 병합합니다.",
    )

    batch = commands.add_parser(
        "label-batch",
        parents=[common],
        help="특정 miss 하위폴더만 YOLO 자동라벨 후 CVAT에 올립니다.",
    )
    batch.add_argument(
        "folder",
        help="예: miss/20261111-2 또는 F:/dog_db/detect/miss/20261111-2",
    )
    batch.add_argument("--conf", type=float, default=None, help="YOLO conf (기본 0.15)")
    batch.add_argument("--model", type=str, default=None, help="weights 경로 (기본 best.pt)")

    merge_neg = commands.add_parser(
        "merge-negatives",
        parents=[common],
        help="기존 reviewed 검수본에 강아지 없는 miss를 빈 라벨로 병합합니다.",
    )
    merge_neg.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="특정 폴더만 (예: miss/20261112-1). 생략 시 miss 전체.",
    )

    train = commands.add_parser(
        "train",
        parents=[common],
        help="검수본으로 YOLO11n을 학습합니다.",
    )
    train.add_argument("--from-autolabel", action="store_true")
    train.add_argument("--allow-other-gpu", action="store_true")
    train.add_argument(
        "--finetune",
        action="store_true",
        help="기존 runs/dog-yolo11n/weights/best.pt 에서 이어서 학습합니다.",
    )

    commands.add_parser("status", parents=[common], help="상태 출력")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    from dog_detect.config import load_config

    cfg = load_config(args.config)

    if args.command == "import-maix":
        from maxi_dog_detect.import_maix import import_maix

        import_maix(cfg)
        return 0

    if args.command == "autolabel-empty":
        from maxi_dog_detect.autolabel_empty import autolabel_empty

        prefix = "ok" if args.ok else (None if args.all_empty else "miss")
        autolabel_empty(
            cfg,
            miss_only=not args.all_empty and not args.ok,
            overwrite=args.overwrite,
            prefix=prefix,
        )
        return 0

    if args.command == "discard-empty":
        from maxi_dog_detect.discard_empty import discard_empty

        discard_empty(cfg, include_cat=not args.keep_cat)
        return 0

    if args.command == "cvat-push":
        from dog_detect.cvat_io import push_autolabels

        push_autolabels(cfg)
        return 0

    if args.command == "cvat-pull":
        if args.merge:
            from maxi_dog_detect.merge_pull import merge_pull

            merge_pull(cfg, args.task_ids)
        else:
            from dog_detect.cvat_io import pull_reviewed

            pull_reviewed(cfg, args.task_ids)
        return 0

    if args.command == "label-batch":
        from maxi_dog_detect.label_batch import label_batch

        label_batch(cfg, args.folder, conf=args.conf, model_path=args.model)
        return 0

    if args.command == "merge-negatives":
        from maxi_dog_detect.merge_negatives import merge_negatives

        merge_negatives(cfg, folder=args.folder)
        return 0

    if args.command == "train":
        from dataclasses import replace

        from dog_detect.train import run_train

        if args.finetune:
            weights = cfg.root / "runs" / "dog-yolo11n" / "weights" / "best.pt"
            if not weights.is_file():
                raise SystemExit(f"finetune weights 없음: {weights}")
            cfg = replace(cfg, train=replace(cfg.train, model=str(weights)))
            print(f"finetune from: {weights}")
        run_train(cfg, from_autolabel=args.from_autolabel, allow_other_gpu=args.allow_other_gpu)
        return 0

    if args.command == "status":
        from dog_detect.cli import run_status

        run_status(cfg)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
