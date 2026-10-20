"""dog-detect 명령."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", type=Path, default=None, help="config.yaml 경로")

    parser = argparse.ArgumentParser(
        prog="dog-detect",
        description="저장된 영상에서 강아지를 탐지하고, CVAT 검수 후 RTX 5070에서 YOLO11n을 학습합니다.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    detect = commands.add_parser("detect", parents=[common], help="영상에서 강아지를 탐지하고 라벨을 저장합니다.")
    detect.add_argument("--video", type=Path, default=None, help="영상 파일 또는 폴더. 기본은 data/videos")

    commands.add_parser("cvat-push", parents=[common], help="자동 라벨을 CVAT 태스크로 올립니다.")

    pull = commands.add_parser("cvat-pull", parents=[common], help="CVAT 검수본을 학습 폴더로 내려받습니다.")
    pull.add_argument("--task-id", type=int, action="append", dest="task_ids", help="태스크 id. 반복 지정 가능")

    train = commands.add_parser("train", parents=[common], help="검수본으로 RTX 5070에서 YOLO11n을 학습합니다.")
    train.add_argument(
        "--from-autolabel",
        action="store_true",
        help="검수본 대신 자동 라벨로 시험 학습합니다.",
    )
    train.add_argument(
        "--allow-other-gpu",
        action="store_true",
        help="RTX 5070이 아닌 GPU에서도 학습합니다.",
    )

    gpu = commands.add_parser("gpu", help="RTX 5070과 PyTorch CUDA 지원을 확인합니다.")
    gpu.add_argument(
        "--fix",
        action="store_true",
        help="sm_120이 없으면 CUDA 12.8 이상 PyTorch 휠을 다시 설치합니다.",
    )

    commands.add_parser("status", parents=[common], help="영상, 라벨, CVAT, 학습 가중치 상태를 출력합니다.")
    return parser


def run_gpu(fix: bool) -> int:
    from dog_detect.config import APP_ROOT, _load_env
    from dog_detect.gpu import cuda_status, fix_torch

    _load_env(APP_ROOT)
    ok, message = cuda_status()
    print(message)
    if ok:
        return 0
    if not fix:
        return 1
    fix_torch()
    print("설치를 확인합니다.")
    completed = subprocess.run([sys.executable, "-m", "dog_detect", "gpu"], check=False)
    return completed.returncode


def run_status(cfg) -> None:
    from dog_detect.dataset import count_label_files, list_images, list_videos

    videos = list_videos(cfg.paths.videos) if cfg.paths.videos.exists() else []
    images = list_images(cfg.paths.autolabel / "images")
    nonempty, empty = count_label_files(cfg.paths.autolabel / "labels")
    print(f"영상: {len(videos)}")
    print(f"자동 라벨 이미지: {len(images)} (박스 {nonempty}, 빈 라벨 {empty})")

    state_path = cfg.paths.autolabel / "cvat_task.json"
    if state_path.is_file():
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        tasks = payload.get("tasks", [])
        if not tasks:
            print("CVAT: 태스크 기록이 비어 있습니다.")
        for task in tasks:
            print(f"CVAT: {task.get('url')} ({task.get('images')}장)")
    else:
        print("CVAT: 아직 업로드하지 않았습니다.")

    dataset = cfg.paths.reviewed / "dataset"
    data_yaml = dataset / "data.yaml"
    if data_yaml.is_file():
        train_count = len(list_images(dataset / "images" / "train"))
        val_count = len(list_images(dataset / "images" / "val"))
        print(f"검수 학습셋: train {train_count}, val {val_count}")
    else:
        print("검수 학습셋: 없음")

    best = cfg.paths.runs / "dog-yolo11n" / "weights" / "best.pt"
    print(f"가중치: {best if best.is_file() else '없음'}")


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "gpu":
            return run_gpu(args.fix)

        from dog_detect.config import load_config

        cfg = load_config(args.config)
        if args.command == "detect":
            from dog_detect.detect import run_detect

            run_detect(cfg, args.video)
        elif args.command == "cvat-push":
            from dog_detect.cvat_io import push_autolabels

            push_autolabels(cfg)
        elif args.command == "cvat-pull":
            from dog_detect.cvat_io import pull_reviewed

            pull_reviewed(cfg, args.task_ids)
        elif args.command == "train":
            from dog_detect.train import run_train

            run_train(cfg, args.from_autolabel, args.allow_other_gpu)
        elif args.command == "status":
            run_status(cfg)
        else:
            raise RuntimeError(f"알 수 없는 명령입니다: {args.command}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"명령이 실패했습니다 (exit {exc.returncode}). TORCH_INDEX_URL을 확인하세요.", file=sys.stderr)
        return exc.returncode or 1
    return 0


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))
