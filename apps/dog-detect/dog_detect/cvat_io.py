"""CVAT 프로젝트에 자동 라벨을 올리고, 사람 검수본을 내려받습니다."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from dog_detect.config import AppConfig


YOLO_IMPORT = "YOLO 1.1"
YOLO_EXPORT = "Ultralytics YOLO Detection 1.0"


def task_state_path(cfg: AppConfig) -> Path:
    return cfg.paths.autolabel / "cvat_task.json"


def connect(cfg: AppConfig):
    try:
        from cvat_sdk import make_client
    except ImportError as exc:
        raise RuntimeError("cvat-sdk가 없습니다. scripts/setup.ps1 을 실행하세요.") from exc
    if cfg.cvat.access_token:
        return make_client(cfg.cvat.host, access_token=cfg.cvat.access_token)
    if not cfg.cvat.password:
        raise RuntimeError(
            "CVAT_PASSWORD 또는 CVAT_ACCESS_TOKEN이 없습니다. "
            ".env.example 을 .env로 복사해 값을 넣으세요."
        )
    return make_client(cfg.cvat.host, credentials=(cfg.cvat.username, cfg.cvat.password))


def _as_list(page) -> list:
    if hasattr(page, "results"):
        return list(page.results)
    return list(page)


def _label_names(project) -> list[str]:
    getter = getattr(project, "get_labels", None)
    labels = getter() if callable(getter) else getattr(project, "labels", []) or []
    names: list[str] = []
    for label in labels:
        if isinstance(label, dict):
            names.append(str(label["name"]))
        else:
            names.append(str(label.name))
    return names


def _ensure_format(client, kind: str, name: str) -> None:
    try:
        formats, _response = client.api_client.server_api.retrieve_annotation_formats()
        pool = formats.importers if kind == "import" else formats.exporters
        available = [item.name for item in pool]
    except Exception:
        return
    if name not in available:
        raise RuntimeError(f"CVAT에 '{name}' 형식이 없습니다. 사용 가능: {', '.join(available)}")


def _find_project(client, name: str):
    for project in _as_list(client.projects.list()):
        if project.name == name:
            return project
    return None


def _ensure_project(client, cfg: AppConfig):
    project = _find_project(client, cfg.cvat.project_name)
    if project is None:
        project = client.projects.create(
            {"name": cfg.cvat.project_name, "labels": [{"name": cfg.cvat.label}]}
        )
        print(f"CVAT 프로젝트를 만들었습니다: {cfg.cvat.host}/projects/{project.id}")
    names = _label_names(project)
    if cfg.cvat.label not in names:
        current = ", ".join(names) if names else "(없음)"
        raise RuntimeError(
            f"프로젝트 '{cfg.cvat.project_name}'에 '{cfg.cvat.label}' 라벨이 없습니다. 현재 라벨: {current}"
        )
    return project, names


def _chunks(items: list, size: int):
    if size < 1:
        raise RuntimeError("cvat.chunk_size는 1 이상이어야 합니다.")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _resource_type():
    try:
        from cvat_sdk.core.proxies.tasks import ResourceType
    except ImportError:
        try:
            from cvat_sdk import ResourceType
        except ImportError as exc:
            raise RuntimeError(
                "cvat-sdk에서 ResourceType을 찾지 못했습니다. cvat-sdk 버전을 서버와 맞추세요."
            ) from exc
    return ResourceType


def _write_state(cfg: AppConfig, state: dict) -> None:
    path = task_state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_task_ids(cfg: AppConfig, explicit: list[int] | None) -> list[int]:
    if explicit:
        return explicit
    path = task_state_path(cfg)
    if not path.is_file():
        raise RuntimeError("CVAT 태스크 기록이 없습니다. cvat-push를 실행하거나 --task-id를 지정하세요.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = [int(item["id"]) for item in payload.get("tasks", [])]
    if not ids:
        raise RuntimeError("cvat_task.json에 태스크가 없습니다.")
    return ids


def push_autolabels(cfg: AppConfig) -> None:
    from dog_detect.dataset import list_images
    from dog_detect.yolo_fmt import write_image_zip, write_yolo11_annotation_zip

    images = list_images(cfg.paths.autolabel / "images")
    if not images:
        raise RuntimeError("자동 라벨 이미지가 없습니다. 먼저 detect를 실행하세요.")

    labels_dir = cfg.paths.autolabel / "labels"
    staging = cfg.paths.autolabel / "_cvat"
    staging.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    state: dict | None = None
    resource_type = _resource_type()

    with connect(cfg) as client:
        project, names = _ensure_project(client, cfg)
        dog_index = names.index(cfg.cvat.label)
        _ensure_format(client, "import", YOLO_IMPORT)
        parts = list(_chunks(images, cfg.cvat.chunk_size))
        for index, part in enumerate(parts, start=1):
            task_name = f"{cfg.cvat.task_prefix}-{stamp}-{index:03d}"
            image_zip = staging / f"{task_name}-images.zip"
            anno_zip = staging / f"{task_name}-labels.zip"
            write_image_zip(part, image_zip)
            write_yolo11_annotation_zip(part, labels_dir, anno_zip, names, dog_index)
            print(f"업로드: {task_name} ({len(part)}장)")
            task = client.tasks.create_from_data(
                spec={"name": task_name, "project_id": project.id},
                resource_type=resource_type.LOCAL,
                resources=[str(image_zip)],
            )
            task.import_annotations(YOLO_IMPORT, str(anno_zip))
            url = f"{cfg.cvat.host}/tasks/{task.id}"
            if state is None:
                state = {
                    "created_at": stamp,
                    "project_id": project.id,
                    "project_name": cfg.cvat.project_name,
                    "label": cfg.cvat.label,
                    "tasks": [],
                }
            state["tasks"].append(
                {"id": task.id, "name": task_name, "url": url, "images": len(part)}
            )
            _write_state(cfg, state)
            image_zip.unlink(missing_ok=True)
            anno_zip.unlink(missing_ok=True)
            print(f"검수: {url}")

    shutil.rmtree(staging, ignore_errors=True)
    print("CVAT에서 박스를 수정한 뒤 cvat-pull 을 실행하세요.")


def _export_task(task, zip_path: Path) -> None:
    try:
        task.export_dataset(YOLO_EXPORT, str(zip_path), include_images=True)
    except TypeError:
        task.export_dataset(YOLO_EXPORT, str(zip_path))


def pull_reviewed(cfg: AppConfig, task_ids: list[int] | None) -> Path:
    from dog_detect.dataset import dedupe_pairs, exported_pairs, prepare_dataset, safe_extract

    ids = load_task_ids(cfg, task_ids)
    raw = cfg.paths.reviewed / "raw"
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
    data_yaml = prepare_dataset(
        pairs,
        cfg.paths.reviewed / "dataset",
        cfg.train.val_ratio,
        cfg.train.seed,
        cfg.cvat.label,
    )
    print(f"학습 데이터: {data_yaml}")
    return data_yaml
