"""경로·설정 로드."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    bundled = APP_ROOT / "config.yaml"
    if bundled.exists():
        return bundled
    return Path.cwd() / "config.yaml"


@dataclass(frozen=True)
class Paths:
    videos: Path
    autolabel: Path
    reviewed: Path
    runs: Path


@dataclass(frozen=True)
class DetectSettings:
    model: str
    class_name: str
    conf: float
    iou: float
    imgsz: int
    sample_fps: float
    min_frame_diff: float
    max_gap_seconds: float
    device: str
    save_empty: bool
    min_box_area: float
    max_frames_per_video: int
    batch: int
    jpeg_quality: int


@dataclass(frozen=True)
class CvatSettings:
    host: str
    username: str
    password: str
    access_token: str
    project_name: str
    label: str
    task_prefix: str
    chunk_size: int


@dataclass(frozen=True)
class LiveSettings:
    source: str


@dataclass(frozen=True)
class TrainSettings:
    model: str
    epochs: int
    imgsz: int
    batch: int
    device: str
    workers: int
    amp: bool
    patience: int
    cache: bool
    val_ratio: float
    seed: int


@dataclass(frozen=True)
class AppConfig:
    root: Path
    paths: Paths
    detect: DetectSettings
    live: LiveSettings
    cvat: CvatSettings
    train: TrainSettings


def _load_env(root: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(root / ".env")


def _section(raw: dict, name: str) -> dict:
    value = raw.get(name) or {}
    if not isinstance(value, dict):
        raise RuntimeError(f"config.yaml의 {name}은 맵이어야 합니다.")
    return value


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path


def load_config(path: Path | None = None) -> AppConfig:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML이 없습니다. scripts/setup.ps1 을 실행하세요.") from exc

    config_path = (path or default_config_path()).resolve()
    if not config_path.is_file():
        raise RuntimeError(f"설정 파일이 없습니다: {config_path}")
    root = config_path.parent
    _load_env(root)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise RuntimeError("config.yaml 형식이 올바르지 않습니다.")

    paths_raw = _section(raw, "paths")
    detect_raw = _section(raw, "detect")
    live_raw = _section(raw, "live")
    cvat_raw = _section(raw, "cvat")
    train_raw = _section(raw, "train")

    val_ratio = float(train_raw.get("val_ratio", 0.2))
    if not 0 < val_ratio < 1:
        raise RuntimeError("train.val_ratio는 0과 1 사이여야 합니다.")

    host = os.environ.get("CVAT_HOST", str(cvat_raw.get("host", "http://localhost:8080")))
    username = os.environ.get("CVAT_USERNAME", str(cvat_raw.get("username", "admin")))
    password = os.environ.get("CVAT_PASSWORD", "")
    token = os.environ.get("CVAT_ACCESS_TOKEN", "")

    return AppConfig(
        root=root,
        paths=Paths(
            videos=_resolve(root, str(paths_raw.get("videos", "data/videos"))),
            autolabel=_resolve(root, str(paths_raw.get("autolabel", "data/autolabel"))),
            reviewed=_resolve(root, str(paths_raw.get("reviewed", "data/reviewed"))),
            runs=_resolve(root, str(paths_raw.get("runs", "runs"))),
        ),
        detect=DetectSettings(
            model=str(detect_raw.get("model", "yolo11n.pt")),
            class_name=str(detect_raw.get("class_name", "dog")),
            conf=float(detect_raw.get("conf", 0.4)),
            iou=float(detect_raw.get("iou", 0.5)),
            imgsz=int(detect_raw.get("imgsz", 640)),
            sample_fps=float(detect_raw.get("sample_fps", 1)),
            min_frame_diff=float(detect_raw.get("min_frame_diff", 2.5)),
            max_gap_seconds=float(detect_raw.get("max_gap_seconds", 5)),
            device=str(detect_raw.get("device", "0")),
            save_empty=bool(detect_raw.get("save_empty", False)),
            min_box_area=float(detect_raw.get("min_box_area", 0.0005)),
            max_frames_per_video=int(detect_raw.get("max_frames_per_video", 0)),
            batch=int(detect_raw.get("batch", 8)),
            jpeg_quality=int(detect_raw.get("jpeg_quality", 90)),
        ),
        live=LiveSettings(
            source=str(live_raw.get("source", "rtsp://techfinai.iptime.org/stream1")),
        ),
        cvat=CvatSettings(
            host=host.rstrip("/"),
            username=username,
            password=password,
            access_token=token,
            project_name=str(cvat_raw.get("project_name", "pet-dog-detect")),
            label=str(cvat_raw.get("label", "dog")),
            task_prefix=str(cvat_raw.get("task_prefix", "dog-autolabel")),
            chunk_size=int(cvat_raw.get("chunk_size", 400)),
        ),
        train=TrainSettings(
            model=str(train_raw.get("model", "yolo11n.pt")),
            epochs=int(train_raw.get("epochs", 100)),
            imgsz=int(train_raw.get("imgsz", 640)),
            batch=int(train_raw.get("batch", 16)),
            device=str(train_raw.get("device", "0")),
            workers=int(train_raw.get("workers", 0)),
            amp=bool(train_raw.get("amp", True)),
            patience=int(train_raw.get("patience", 30)),
            cache=bool(train_raw.get("cache", False)),
            val_ratio=val_ratio,
            seed=int(train_raw.get("seed", 42)),
        ),
    )
