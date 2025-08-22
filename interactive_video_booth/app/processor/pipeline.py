from typing import Optional

import cv2
import numpy as np

from app.config.schema import SharedState
from app.processor.detectors import MotionDetector
from app.processor.effects import apply_aura, apply_trails


class ProcessingPipeline:
    def __init__(self, shared: SharedState):
        self.shared = shared
        self.detector = MotionDetector(sensitivity=float(self.shared.get_param("detection.sensitivity", 0.5)))
        self.prev_out: Optional[np.ndarray] = None
        self.last_frame: Optional[np.ndarray] = None

    def process(self, frame: np.ndarray) -> np.ndarray:
        # Update detector sensitivity smoothly if changed
        sens = float(self.shared.get_param("detection.sensitivity", 0.5))
        self.detector = self.detector if sens == getattr(self, "_last_sens", None) else MotionDetector(sensitivity=sens)
        self._last_sens = sens

        mask = self.detector.get_mask(frame)

        effect_type = self.shared.get_param("effect.type", "aura")
        intensity = float(self.shared.get_param("effect.intensity", 0.8))
        hue_shift = float(self.shared.get_param("effect.hue_shift", 0.0))
        trail = float(self.shared.get_param("effect.trail", 0.5))

        out = frame
        if effect_type == "aura":
            out = apply_aura(out, mask, intensity=intensity, hue_shift=hue_shift)
        # More effects could be added here

        out = apply_trails(self.prev_out, out, trail_amount=trail)
        self.prev_out = out
        self.last_frame = out
        return out
