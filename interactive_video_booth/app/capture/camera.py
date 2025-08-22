from __future__ import annotations
import cv2
import time
import threading
from typing import Optional, Tuple, Union


class CameraStream:
    def __init__(self, source: Union[int, str] = 0, fps: int = 30, width: int | None = None, height: int | None = None):
        self.source = source
        self.fps = fps
        self.width = width
        self.height = height
        self.lock = threading.Lock()
        self.frame = None
        self.stopped = True
        self.cap: Optional[cv2.VideoCapture] = None

    def _open(self):
        self.cap = cv2.VideoCapture(self.source)
        if self.width and self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.fps:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

    def start(self):
        self._open()
        self.stopped = False
        threading.Thread(target=self._loop, daemon=True).start()
        return self

    def _loop(self):
        retry_backoff = 0.5
        while not self.stopped:
            if self.cap is None or not self.cap.isOpened():
                try:
                    self._open()
                except Exception:
                    time.sleep(retry_backoff)
                    retry_backoff = min(2.0, retry_backoff * 1.5)
                    continue
            ok, frame = self.cap.read()
            if not ok:
                # reconnect
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame
            time.sleep(max(0, 1.0 / self.fps - 0.001))

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.stopped = True
        if self.cap is not None:
            self.cap.release()
            self.cap = None
