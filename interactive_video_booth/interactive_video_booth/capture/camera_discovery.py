from __future__ import annotations
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import cv2  # type: ignore

from ..utils.logger import get_logger, write_error_log
from ..utils.errors import StageError


@dataclass
class CameraReport:
    source: str
    resolution: Tuple[int, int]
    fps_est: float
    frames_ok_pct: float
    controls_supported: List[str]
    flaky: bool


def _load_camera_sources(configs_dir: Path) -> Dict[str, List[str]]:
    cfg_file = configs_dir / "camera_sources.json"
    if not cfg_file.exists():
        return {"preferred": [], "fallbacks": []}
    try:
        with cfg_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        preferred = data.get("preferred", [])
        fallbacks = data.get("fallbacks", [])
        return {"preferred": preferred, "fallbacks": fallbacks}
    except Exception:
        return {"preferred": [], "fallbacks": []}


def _parse_source(src: str | int) -> tuple[str, int | str]:
    """Return a display string and the value to pass to OpenCV.

    - int indices (0..N) or strings like '0' -> as int
    - 'usb:N' -> N as int
    - rtsp/http/file paths remain strings
    """
    if isinstance(src, int):
        return (str(src), src)
    s = str(src).strip()
    if s.lower().startswith("usb:"):
        try:
            idx = int(s.split(":", 1)[1])
            return (s, idx)
        except Exception:
            return (s, s)
    # numeric string
    if s.isdigit():
        return (s, int(s))
    return (s, s)


def _try_open(source: str | int) -> Optional[cv2.VideoCapture]:
    disp, ocv_src = _parse_source(source)
    cap = cv2.VideoCapture(ocv_src)
    if cap is None or not cap.isOpened():
        try:
            cap.release()
        except Exception:
            pass
        return None
    return cap


def _test_capture(cap: cv2.VideoCapture, timeout_sec: float = 3.0, target_frames: int = 60) -> Tuple[float, float, Tuple[int, int]]:
    start = time.time()
    frames = 0
    ok_frames = 0
    while (time.time() - start) < timeout_sec and frames < target_frames:
        ret, frame = cap.read()
        frames += 1
        if ret and frame is not None and frame.size > 0:
            ok_frames += 1
    elapsed = max(time.time() - start, 1e-6)
    fps_est = ok_frames / elapsed
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
    return fps_est, (ok_frames / max(frames, 1)) * 100.0, (w, h)


def _probe_controls(cap: cv2.VideoCapture) -> List[str]:
    supported: List[str] = []
    # Exposure
    try:
        val = cap.get(cv2.CAP_PROP_EXPOSURE)
        if val != -1 and val is not None:
            supported.append("exposure")
    except Exception:
        pass
    # Gain
    try:
        val = cap.get(cv2.CAP_PROP_GAIN)
        if val != -1 and val is not None:
            supported.append("gain")
    except Exception:
        pass
    # Frame size
    try:
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if w and h:
            supported.append("resolution")
    except Exception:
        pass
    return supported


def discover_and_validate_camera(base_dir: Path, device: Optional[str] = None, force: bool = False) -> CameraReport:
    stage_label = "STAGE 1"
    log = get_logger(stage_label, base_dir)

    sources: List[str | int] = []

    if device:
        sources.append(device)

    # USB indices 0..4
    for i in range(5):
        sources.append(i)

    # Config file
    cfg = _load_camera_sources(base_dir / "configs")
    sources.extend(cfg.get("preferred", []))
    sources.extend(cfg.get("fallbacks", []))

    tried: List[str] = []
    best_report: Optional[CameraReport] = None

    for src in sources:
        disp, ocv_src = _parse_source(src)
        if disp in tried:
            continue
        tried.append(disp)
        cap = _try_open(ocv_src)
        if cap is None:
            continue
        try:
            fps_est, ok_pct, (w, h) = _test_capture(cap)
            controls = _probe_controls(cap)
            flaky = ok_pct < 80.0
            report = CameraReport(
                source=disp,
                resolution=(w, h),
                fps_est=float(f"{fps_est:.2f}"),
                frames_ok_pct=float(f"{ok_pct:.1f}"),
                controls_supported=controls if controls else ["CAMCTRL: not supported"],
                flaky=flaky,
            )
            # save best (prefer non-flaky)
            if best_report is None or (best_report.flaky and not report.flaky) or (not report.flaky and report.fps_est > best_report.fps_est):
                best_report = report
            cap.release()
        except Exception:
            try:
                cap.release()
            except Exception:
                pass
            continue

    if best_report is None:
        msg = "No reliable camera source found"
        write_error_log(stage_label, base_dir, "stage1_failure_report.txt", msg + "\nTried: " + ", ".join(tried))
        raise StageError(10, msg)

    # Persist report and last camera
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    with (logs_dir / "camera_report.json").open("w", encoding="utf-8") as f:
        json.dump(asdict(best_report), f, indent=2)

    (base_dir / "configs").mkdir(parents=True, exist_ok=True)
    with (base_dir / "configs" / "last_camera.json").open("w", encoding="utf-8") as f:
        json.dump({"source": best_report.source, "camera_mode": "flaky" if best_report.flaky else "normal"}, f, indent=2)

    # Console line
    res_w, res_h = best_report.resolution
    log.info(
        f"Camera found: index={best_report.source} resolution={res_w}x{res_h} "
        f"fps={best_report.fps_est} frames_ok_pct={best_report.frames_ok_pct} "
        f"controls_supported={best_report.controls_supported}"
    )

    if best_report.flaky and not force:
        warn = (
            "Only flaky camera(s) found. Use --force to continue. GUI will mark camera_mode=flaky."
        )
        write_error_log(stage_label, base_dir, "stage1_failure_report.txt", warn)
        raise StageError(10, "No reliable camera source found (best candidate flaky)")

    return best_report
