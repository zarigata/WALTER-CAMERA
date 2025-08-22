from __future__ import annotations
import numpy as np
import cv2


class SimpleTracker:
    """Placeholder for multi-person tracking.
    Currently extracts largest contour as primary person and persists it.
    """

    def __init__(self, persistence_frames: int = 10):
        self.N = persistence_frames
        self.prev_contour = None
        self.miss = 0

    def update(self, mask: np.ndarray) -> np.ndarray:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            self.prev_contour = largest
            self.miss = 0
        else:
            if self.prev_contour is not None and self.miss < self.N:
                self.miss += 1
            else:
                self.prev_contour = None
        out = np.zeros_like(mask)
        if self.prev_contour is not None:
            cv2.drawContours(out, [self.prev_contour], -1, 255, thickness=cv2.FILLED)
        return out
