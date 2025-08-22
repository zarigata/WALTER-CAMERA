import cv2
import numpy as np

from app.processor.effects import apply_aura


def test_apply_aura_runs():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mask = np.zeros((240, 320), dtype=np.uint8)
    cv2.circle(mask, (160, 120), 60, 255, -1)
    out = apply_aura(frame, mask, intensity=0.8, hue_shift=0.1)
    assert out.shape == frame.shape
