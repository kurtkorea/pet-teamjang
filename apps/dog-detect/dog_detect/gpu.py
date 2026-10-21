"""RTX 5070(Blackwell sm_120)에서 CUDA가 실제로 쓰이는지 확인합니다."""

from __future__ import annotations

import os
import subprocess
import sys


def nvidia_smi_line() -> str:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,compute_cap",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=20,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return output.strip()


def _parse_sm(token: str) -> tuple[int, int] | None:
    for prefix in ("sm_", "compute_"):
        if token.startswith(prefix):
            digits = token[len(prefix) :]
            if digits.isdigit() and len(digits) >= 2:
                return int(digits[:-1]), int(digits[-1])
    return None


def _arch_supported(device_major: int, device_minor: int, compiled: set[str]) -> bool:
    """공식 PyTorch 휠은 Ada(sm_89)를 목록에 넣지 않고 sm_86/sm_80으로 돌립니다."""
    exact = f"sm_{device_major}{device_minor}"
    if exact in compiled or f"compute_{device_major}{device_minor}" in compiled:
        return True
    for token in compiled:
        parsed = _parse_sm(token)
        if parsed is None:
            continue
        major, minor = parsed
        # 같은 major에서 같거나 낮은 minor면 SASS 호환(예: sm_89 ← sm_86).
        if major == device_major and minor <= device_minor:
            return True
    return False


def _arch_ready(torch_module) -> tuple[bool, str]:
    if not torch_module.cuda.is_available():
        return False, "CUDA를 사용할 수 없습니다. NVIDIA 드라이버 설치 여부를 확인하세요."
    major, minor = torch_module.cuda.get_device_capability(0)
    arch = f"sm_{major}{minor}"
    compiled = set(torch_module.cuda.get_arch_list())
    name = torch_module.cuda.get_device_name(0)
    props = torch_module.cuda.get_device_properties(0)
    vram_gb = props.total_memory / (1024**3)
    summary = f"{name} | {arch} | {vram_gb:.1f} GB | torch {torch_module.__version__}"
    if not _arch_supported(major, minor, compiled):
        supported = ", ".join(sorted(compiled)) or "(없음)"
        return False, (
            f"{summary}\n"
            f"이 PyTorch 빌드에는 {arch}가 없습니다. 들어 있는 아키텍처: {supported}"
        )
    return True, summary


def cuda_status() -> tuple[bool, str]:
    lines = []
    smi = nvidia_smi_line()
    if smi:
        lines.append(f"nvidia-smi: {smi}")
    try:
        import torch
    except ImportError:
        lines.append("PyTorch가 없습니다. scripts/setup.ps1 을 실행하세요.")
        return False, "\n".join(lines)
    ok, detail = _arch_ready(torch)
    lines.append(detail)
    return ok, "\n".join(lines)


def assert_trainable(allow_other: bool) -> str:
    """학습 가능한 RTX 5070이면 GPU 이름 한 줄을 돌려줍니다."""
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch가 없습니다. scripts/setup.ps1 을 실행하세요.") from exc
    ok, detail = _arch_ready(torch)
    if not ok:
        raise RuntimeError(detail + "\npython -m dog_detect gpu --fix 를 실행하세요.")
    name = torch.cuda.get_device_name(0)
    if "5070" not in name and not allow_other:
        raise RuntimeError(
            f"학습 GPU는 RTX 5070이어야 합니다. 현재 GPU는 {name} 입니다. "
            "이 GPU로 진행하려면 --allow-other-gpu 를 사용하세요."
        )
    return detail


def fix_torch() -> None:
    index = os.environ.get("TORCH_INDEX_URL", "https://download.pytorch.org/whl/cu128")
    print(f"PyTorch CUDA 휠을 설치합니다: {index}")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            "torch",
            "torchvision",
            "torchaudio",
            "--index-url",
            index,
        ]
    )


def resolve_detect_device(requested: str) -> str:
    if requested.lower() == "cpu":
        return "cpu"
    ok, detail = cuda_status()
    print(detail)
    if ok:
        return requested
    raise RuntimeError(
        "RTX 5070에서 탐지하려면 CUDA용 PyTorch가 필요합니다. "
        "python -m dog_detect gpu --fix 를 실행하세요. "
        "CPU로 돌리려면 config.yaml의 detect.device를 cpu로 두세요."
    )
