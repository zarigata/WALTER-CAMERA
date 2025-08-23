from __future__ import annotations
import sys
import importlib
from pathlib import Path
from typing import List

from .logger import get_logger, write_error_log
from .errors import StageError


REQUIRED_IMPORTS: List[str] = [
    "cv2",
    "numpy",
    "psutil",
    "onnxruntime",
    "imageio",
]

OPTIONAL_IMPORTS: List[str] = [
    "torch",
]


def _check_python_version() -> None:
    # Enforce Python 3.11.x for compatibility
    if not (sys.version_info.major == 3 and sys.version_info.minor == 11):
        raise StageError(2, f"Python 3.11.x required; detected {sys.version_info.major}.{sys.version_info.minor}")


def _check_packages() -> List[str]:
    missing: List[str] = []
    for mod in REQUIRED_IMPORTS:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    return missing


def _gpu_status() -> str:
    cuda_available = False
    onnx_ep = []

    # Check PyTorch CUDA if available
    try:
        torch = importlib.import_module("torch")
        if hasattr(torch, "cuda") and callable(getattr(torch.cuda, "is_available", None)):
            cuda_available = bool(torch.cuda.is_available())
    except Exception:
        pass

    # Check ONNX Runtime providers
    try:
        ort = importlib.import_module("onnxruntime")
        onnx_ep = getattr(ort, "get_available_providers", lambda: [])()
        if "CUDAExecutionProvider" in onnx_ep:
            cuda_available = True
    except Exception:
        pass

    return "CUDA available" if cuda_available else "None - using CPU"


def _ensure_dirs_writable(base_dir: Path) -> None:
    dirs = ["logs", "configs", "models", "outputs"]
    for d in dirs:
        p = base_dir / d
        p.mkdir(parents=True, exist_ok=True)
        # try touch a temp file to ensure writability
        tf = p / ".writable_test"
        try:
            tf.write_text("ok", encoding="utf-8")
            tf.unlink(missing_ok=True)
        except Exception as e:
            raise StageError(4, f"Directory not writable: {p} -> {e}")


def run_stage0(base_dir: Path) -> int:
    stage_label = "STAGE 0"
    log = get_logger(stage_label, base_dir)
    try:
        _check_python_version()
        log.info(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

        missing = _check_packages()
        if missing:
            msg = f"Missing packages: {', '.join(missing)}"
            log.info(msg)
            write_error_log(stage_label, base_dir, "stage0_error.log", msg)
            raise StageError(3, msg)
        else:
            log.info("Missing packages: none")

        gpu = _gpu_status()
        log.info(f"GPU: {gpu}")

        # If GPU not available, ensure ONNX CPU EP exists
        try:
            import onnxruntime as ort  # type: ignore
            providers = ort.get_available_providers()
            if "CPUExecutionProvider" not in providers:
                msg = "ONNX Runtime CPUExecutionProvider not available"
                write_error_log(stage_label, base_dir, "stage0_error.log", msg)
                raise StageError(3, msg)
        except Exception as e:
            msg = f"ONNX Runtime not importable: {e}"
            write_error_log(stage_label, base_dir, "stage0_error.log", msg)
            raise StageError(3, msg)

        if gpu == "None - using CPU":
            log.info("WARNING: GPU not available. Proceeding in CPU-only mode; expect lower FPS.")

        _ensure_dirs_writable(base_dir)
        log.info("Directories created: logs/, configs/, models/, outputs/")
        return 0
    except StageError as se:
        # Already logged
        print(f"[STAGE 0] ERROR: {se.message}")
        raise
