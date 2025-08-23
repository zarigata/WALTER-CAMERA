from __future__ import annotations
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def _pip_freeze() -> List[str]:
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def create_env_snapshot(base_dir: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    # Python and OS
    data["python"] = {
        "version": sys.version,
        "executable": sys.executable,
    }
    data["platform"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    # Key libraries
    def _version(modname: str) -> str | None:
        try:
            mod = __import__(modname)
            return getattr(mod, "__version__", None)
        except Exception:
            return None

    data["packages"] = {
        "numpy": _version("numpy"),
        "opencv_python": _version("cv2"),
        "onnxruntime": _version("onnxruntime"),
        "psutil": _version("psutil"),
        "requests": _version("requests"),
    }

    # ONNX Runtime providers (if available)
    try:
        import onnxruntime as ort  # type: ignore

        data["onnxruntime_providers"] = {
            "available": list(ort.get_available_providers()),
            "default": list(ort.get_available_providers()),
        }
    except Exception:
        data["onnxruntime_providers"] = {
            "available": [],
            "default": [],
        }

    # Pip freeze lock
    lock_lines = _pip_freeze()
    (base_dir / "requirements.lock.txt").write_text("\n".join(lock_lines) + "\n", encoding="utf-8")

    # Write json snapshot
    out = base_dir / "configs" / "env_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
