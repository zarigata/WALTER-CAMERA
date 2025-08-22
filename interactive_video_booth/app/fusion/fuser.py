from __future__ import annotations
import numpy as np
import cv2


class MaskFuser:
    def __init__(self, seg_weight: float = 0.6, motion_weight: float = 0.4, on_th: float = 0.4, off_th: float = 0.2, persistence_frames: int = 10):
        self.seg_w = seg_weight
        self.motion_w = motion_weight
        self.on_th = on_th
        self.off_th = off_th
        self.N = persistence_frames
        self.prev_mask = None
        self.prev_frame = None
        self.miss_count = 0

    def _warp_prev(self, prev_frame, prev_mask, frame):
        try:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 2, 15, 2, 5, 1.1, 0)
            h, w = gray.shape
            grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
            map_x = (grid_x + flow[..., 0]).astype(np.float32)
            map_y = (grid_y + flow[..., 1]).astype(np.float32)
            warped = cv2.remap(prev_mask, map_x, map_y, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            return warped
        except Exception:
            return prev_mask

    def fuse(self, frame, seg_mask: np.ndarray, conf_map: np.ndarray) -> np.ndarray:
        seg_norm = (seg_mask.astype(np.float32) / 255.0)
        fused = self.seg_w * seg_norm + self.motion_w * conf_map
        th = self.on_th if self.prev_mask is None else self.off_th
        fused_bin = (fused >= th).astype(np.uint8) * 255

        # Persistence and anti-blink
        if self.prev_mask is not None:
            # If current detection is weak, keep warped previous mask for N frames
            if np.count_nonzero(fused_bin) < 200 and self.miss_count < self.N:
                warped = self._warp_prev(self.prev_frame, self.prev_mask, frame)
                fused_bin = cv2.bitwise_or(fused_bin, warped)
                self.miss_count += 1
            else:
                self.miss_count = 0

        # Smooth edges
        fused_bin = cv2.morphologyEx(fused_bin, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        fused_bin = cv2.morphologyEx(fused_bin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        self.prev_mask = fused_bin.copy()
        self.prev_frame = frame.copy()
        return fused_bin
