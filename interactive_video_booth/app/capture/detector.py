import platform
from typing import Dict, List, Optional, Tuple

import cv2


def _backend_preferences() -> List[Optional[int]]:
    sys = platform.system().lower()
    prefs: List[Optional[int]]
    if sys == "windows":
        prefs = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
    elif sys == "darwin":
        prefs = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
    else:  # linux/other
        prefs = [cv2.CAP_V4L2, cv2.CAP_ANY]
    return prefs


def _try_open(index: int, api_pref: Optional[int]) -> Optional[Dict]:
    try:
        cap = cv2.VideoCapture(index, api_pref) if api_pref is not None else cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            return None
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            return None
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        backend = int(cap.get(cv2.CAP_PROP_BACKEND)) if hasattr(cv2, 'CAP_PROP_BACKEND') else (api_pref or 0)
        cap.release()
        return {
            "index": index,
            "backend": backend,
            "width": w,
            "height": h,
            "fps": fps,
        }
    except Exception:
        try:
            cap.release()
        except Exception:
            pass
        return None


def list_cameras(max_index: int = 15) -> List[Dict]:
    found: List[Dict] = []
    prefs = _backend_preferences()
    seen = set()
    for i in range(0, max(0, max_index) + 1):
        entry: Optional[Dict] = None
        for api in prefs:
            entry = _try_open(i, api)
            if entry:
                break
        if entry:
            key = (entry["index"], entry["backend"])
            if key not in seen:
                seen.add(key)
                found.append(entry)
    return found


def format_camera_label(entry: Dict) -> str:
    idx = entry.get("index")
    be = entry.get("backend")
    w = entry.get("width")
    h = entry.get("height")
    fps = entry.get("fps")
    return f"Index {idx} | backend {be} | {w}x{h} @ {fps:.0f}fps"
