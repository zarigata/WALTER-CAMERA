from __future__ import annotations
from typing import List, Tuple


def get_available_providers() -> List[str]:
    try:
        import onnxruntime as ort  # type: ignore
        return list(ort.get_available_providers())
    except Exception:
        return []


def select_onnx_providers(prefer_gpu: bool = True) -> Tuple[List[str], str]:
    """Return (providers_list, selected_label) for ONNX Runtime.

    If prefer_gpu is True and CUDA EP is available -> ["CUDAExecutionProvider", "CPUExecutionProvider"].
    If CUDA not available and DML available -> ["DmlExecutionProvider", "CPUExecutionProvider"].
    If neither CUDA nor DML, but OpenVINO EP available -> ["OpenVINOExecutionProvider", "CPUExecutionProvider"].
    Otherwise -> ["CPUExecutionProvider"].

    If DirectML EP is available on Windows and CUDA is not, prefer it when prefer_gpu=True.
    """
    providers = get_available_providers()
    selected: List[str]
    label = "cpu"

    if prefer_gpu:
        if "CUDAExecutionProvider" in providers:
            selected = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            label = "cuda"
        elif "DmlExecutionProvider" in providers:  # Windows DirectML
            selected = ["DmlExecutionProvider", "CPUExecutionProvider"]
            label = "directml"
        elif "OpenVINOExecutionProvider" in providers:
            selected = ["OpenVINOExecutionProvider", "CPUExecutionProvider"]
            label = "openvino"
        else:
            selected = ["CPUExecutionProvider"]
            label = "cpu"
    else:
        if "OpenVINOExecutionProvider" in providers:
            selected = ["OpenVINOExecutionProvider", "CPUExecutionProvider"]
            label = "openvino"
        else:
            selected = ["CPUExecutionProvider"]
            label = "cpu"

    return selected, label
