from __future__ import annotations
import cv2
import numpy as np


class Segmenter:
    """
    Baseline CPU segmenter using background subtraction + motion cues.
    Produces a binary mask and a pseudo confidence map.
    Swap with GPU model later.
    """

    def __init__(self, history: int = 200, var_threshold: float = 16.0, detect_shadows: bool = False):
        self.bg = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=var_threshold, detectShadows=detect_shadows)
        self.prev_gray = None

    def apply(self, frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        h, w = frame_bgr.shape[:2]
        fg = self.bg.apply(frame_bgr)
        fg = cv2.medianBlur(fg, 5)
        _, fg_bin = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        fg_bin = cv2.morphologyEx(fg_bin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_bin = cv2.morphologyEx(fg_bin, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        motion = np.zeros_like(gray)
        if self.prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(self.prev_gray, gray, None, pyr_scale=0.5, levels=2, winsize=15, iterations=2, poly_n=5, poly_sigma=1.1, flags=0)
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        self.prev_gray = gray
        _, motion_bin = cv2.threshold(motion, 25, 255, cv2.THRESH_BINARY)
        motion_bin = cv2.medianBlur(motion_bin, 5)

        # Confidence proxy: combine fg score (0/255) and motion magnitude
        conf = 0.6 * (fg.astype(np.float32) / 255.0) + 0.4 * (motion.astype(np.float32) / 255.0)
        conf = np.clip(conf, 0, 1)
        return fg_bin, conf
