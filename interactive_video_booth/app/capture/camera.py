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

    def _open(self, timeout_s: float = 3.0):
        backends = []
        # Try platform-specific preferred backends
        backends.extend([cv2.CAP_MSMF, cv2.CAP_DSHOW])
        # Fallback to default (0) by using constructor without apiPreference

        tried = []
        for api in backends + [None]:
            try:
                cap = cv2.VideoCapture(self.source) if api is None else cv2.VideoCapture(self.source, api)
                start = time.time()
                # Apply common properties
                if self.width and self.height:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                # IMPORTANT: Avoid CAP_PROP_FPS on many Windows webcam drivers (can hang)
                if self.fps and isinstance(self.source, str):
                    cap.set(cv2.CAP_PROP_FPS, self.fps)
                # Some drivers expose buffersize (ignore errors)
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
                except Exception:
                    pass
                # Wait until opened and first frame available or timeout
                ok_open = cap.isOpened()
                ok_read = False
                while time.time() - start < timeout_s:
                    if not ok_open:
                        time.sleep(0.05)
                        ok_open = cap.isOpened()
                        continue
                    ok_read, _ = cap.read()
                    if ok_read:
                        break
                    time.sleep(0.05)
                if ok_open and ok_read:
                    self.cap = cap
                    return
                cap.release()
                tried.append(api)
            except Exception:
                tried.append(api)
                try:
                    cap.release()
                except Exception:
                    pass
                continue
        # If all attempts failed, leave cap as None and let loop retry
        self.cap = None

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
