import math
from typing import Optional

import cv2
import numpy as np


def apply_aura(frame: np.ndarray, mask: np.ndarray, intensity: float = 0.8, hue_shift: float = 0.0) -> np.ndarray:
    h, w = frame.shape[:2]
    # Soften mask and create glow via distance transform approximation
    mask_f = cv2.GaussianBlur(mask, (0, 0), sigmaX=8)
    mask_norm = np.clip(mask_f.astype(np.float32) / 255.0, 0.0, 1.0)
    glow = cv2.GaussianBlur(mask_norm, (0, 0), sigmaX=25)

    # Create color aura around subject with hue shift
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 0] = (hsv[:, :, 0] + (hue_shift * 90.0)) % 180.0  # hue range [0,180]
    aura_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    glow3 = np.dstack([glow, glow, glow])
    out = frame.astype(np.float32) * (1.0 - glow3 * intensity) + aura_bgr * (glow3 * intensity)
    out = np.clip(out, 0, 255).astype(np.uint8)

    return out


def apply_trails(prev_out: Optional[np.ndarray], current: np.ndarray, trail_amount: float = 0.5) -> np.ndarray:
    if prev_out is None:
        return current
    alpha = np.clip(trail_amount, 0.0, 1.0)
    return cv2.addWeighted(current, 1.0, prev_out, alpha, 0.0)
