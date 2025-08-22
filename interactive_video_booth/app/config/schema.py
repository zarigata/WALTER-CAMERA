import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULTS = {
    "capture": {"width": 1280, "height": 720, "fps": 30, "rtsp_latency": 0},
    "detection": {"sensitivity": 0.5, "mode": "mog2"},
    "effect": {"type": "aura", "intensity": 0.8, "hue_shift": 0.0, "trail": 0.5},
    "recording": {"duration_s": 12, "codec": "mp4v"},
    "network": {"ws_port": 8765, "host": "0.0.0.0"},
    "postprocess": {"template_id": "default", "event_name": "Event", "description": "", "overlay_path": "assets/overlay.png"},
}


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return DEFAULTS.copy()
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # merge defaults
    merged = json.loads(json.dumps(DEFAULTS))
    for k, v in data.items():
        if isinstance(v, dict) and k in merged:
            merged[k].update(v)
        else:
            merged[k] = v
    return merged


@dataclass
class SharedState:
    config: Dict[str, Any]
    params: Dict[str, Any] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)
    countdown_active: bool = False
    countdown_end_time: float = 0.0
    record_request: bool = False

    def __post_init__(self):
        self.params = {
            # Flattened runtime params for easy slider mapping
            "detection.sensitivity": self.config.get("detection", {}).get("sensitivity", 0.5),
            "detection.mode": self.config.get("detection", {}).get("mode", "mog2"),
            "effect.type": self.config.get("effect", {}).get("type", "aura"),
            "effect.intensity": self.config.get("effect", {}).get("intensity", 0.8),
            "effect.hue_shift": self.config.get("effect", {}).get("hue_shift", 0.0),
            "effect.trail": self.config.get("effect", {}).get("trail", 0.5),
            "recording.duration_s": self.config.get("recording", {}).get("duration_s", 12),
            "postprocess.template_id": self.config.get("postprocess", {}).get("template_id", "default"),
            "postprocess.event_name": self.config.get("postprocess", {}).get("event_name", "Event"),
            "postprocess.description": self.config.get("postprocess", {}).get("description", ""),
        }

    def set_param(self, key: str, value: Any):
        with self.lock:
            self.params[key] = value

    def get_param(self, key: str, default: Any = None) -> Any:
        with self.lock:
            return self.params.get(key, default)

    def start_countdown(self, seconds: int):
        with self.lock:
            self.countdown_active = True
            self.countdown_end_time = time.time() + seconds

    def clear_countdown(self):
        with self.lock:
            self.countdown_active = False
            self.countdown_end_time = 0.0
