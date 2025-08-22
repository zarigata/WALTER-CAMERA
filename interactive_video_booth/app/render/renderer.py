from __future__ import annotations
import cv2
import numpy as np


class Renderer:
    def __init__(self, width: int, height: int, fullscreen: bool = True, window_name: str = "Silhouette Booth", effect: str = "glow"):
        self.w = width
        self.h = height
        self.fullscreen = fullscreen
        self.window_name = window_name
        self.effect = effect
        cv2.namedWindow(self.window_name, cv2.WND_PROP_FULLSCREEN)
        if self.fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def _apply_effect(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        overlay = np.zeros_like(frame)
        color = (0, 255, 255)
        if self.effect == "glow":
            dil = cv2.dilate(mask, np.ones((9, 9), np.uint8))
            blur = cv2.GaussianBlur(dil, (21, 21), 0)
            glow = cv2.applyColorMap(blur, cv2.COLORMAP_AUTUMN)
            overlay = cv2.addWeighted(frame, 1.0, glow, 0.6, 0)
        elif self.effect == "density":
            heat = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
            overlay = cv2.addWeighted(frame, 0.6, heat, 0.7, 0)
        else:  # trails placeholder
            edges = cv2.Canny(mask, 50, 150)
            overlay = frame.copy()
            overlay[edges > 0] = color
        # Draw outline
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (255, 255, 255), thickness=2)
        return overlay

    def render(self, frame_bgr: np.ndarray, mask: np.ndarray):
        frame_resized = cv2.resize(frame_bgr, (self.w, self.h))
        mask_resized = cv2.resize(mask, (self.w, self.h), interpolation=cv2.INTER_NEAREST)
        out = self._apply_effect(frame_resized, mask_resized)
        cv2.imshow(self.window_name, out)

    def close(self):
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass
