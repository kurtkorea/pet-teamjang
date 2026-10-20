"""프레임 간격과 추론 생략 판단. OpenCV에 의존하지 않습니다."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def frame_step(fps: float, sample_fps: float) -> int:
    """원본 fps에서 sample_fps로 줄일 때 건너뛸 프레임 수."""
    if sample_fps <= 0:
        raise ValueError("sample_fps는 0보다 커야 합니다.")
    effective = fps if fps > 0 else 30.0
    return max(1, int(round(effective / sample_fps)))


def should_infer(
    elapsed_since_infer: float,
    mean_abs_diff: float | None,
    min_diff: float,
    max_gap: float,
) -> bool:
    """변화가 작으면 추론을 건너뛰고, max_gap이 지나면 다시 추론합니다."""
    if min_diff <= 0:
        return True
    if mean_abs_diff is None or mean_abs_diff >= min_diff:
        return True
    if max_gap <= 0:
        return False
    return elapsed_since_infer >= max_gap


def frame_stem(video: Path, frame_index: int) -> str:
    """영상 경로가 달라도 파일명이 겹치지 않는 프레임 이름."""
    digest = hashlib.sha1(str(video.resolve()).encode()).hexdigest()[:8]
    safe = re.sub(r"[^\w.-]+", "_", video.stem)[:40].strip("._") or "video"
    return f"{safe}_{digest}_f{frame_index:06d}"
