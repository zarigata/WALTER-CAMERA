from typing import Optional, Tuple

import cv2
import numpy as np


class MotionDetector:
    def __init__(self, sensitivity: float = 0.5):
        self.bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=max(4, int(32 * (1.0 - sensitivity))), detectShadows=False)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def get_mask(self, frame: np.ndarray) -> np.ndarray:
        fg = self.bg.apply(frame)
        fg = cv2.medianBlur(fg, 5)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, self.kernel, iterations=1)
        fg = cv2.morphologyEx(fg, cv2.MORPH_DILATE, self.kernel, iterations=2)
        _, mask = cv2.threshold(fg, 64, 255, cv2.THRESH_BINARY)
        return mask
