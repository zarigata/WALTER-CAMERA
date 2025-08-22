import threading
import time
from typing import Optional, Union

import cv2
import numpy as np


class Camera:
    def __init__(self, source: Union[int, str] = 0, width: int = 1280, height: int = 720, fps: int = 30, api_backend: Optional[int] = None):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.api_backend = api_backend
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.latest_frame: Optional[np.ndarray] = None

    def start(self):
        # Open with specific backend if provided
        if self.api_backend is None:
            self.cap = cv2.VideoCapture(self.source)
        else:
            self.cap = cv2.VideoCapture(self.source, self.api_backend)
        # Apply properties if possible
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        target_delay = 1.0 / max(1, self.fps)
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.05)
                continue
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            self.latest_frame = frame
            # minimal pacing to avoid spin
            time.sleep(0.001)

    def read(self) -> Optional[np.ndarray]:
        return self.latest_frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
