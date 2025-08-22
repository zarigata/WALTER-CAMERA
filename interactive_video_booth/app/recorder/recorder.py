import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

from app.config.schema import SharedState
from app.postprocess.postprocess import postprocess_recording


class Recorder:
    def __init__(self, shared: SharedState, fps: int = 30):
        self.shared = shared
        self.fps = fps
        self.is_recording = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start_after_countdown(self, duration_s: int, frame_provider: Callable[[], Optional[np.ndarray]]):
        if self.is_recording:
            return
        # Wait until countdown finishes
        def run():
            # Wait until countdown clears
            while True:
                if not self.shared.countdown_active:
                    break
                remaining = self.shared.countdown_end_time - time.time()
                if remaining <= 0:
                    break
                time.sleep(0.05)
            self.shared.clear_countdown()
            self._record(duration_s, frame_provider)
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _record(self, duration_s: int, frame_provider: Callable[[], Optional[np.ndarray]]):
        self.is_recording = True
        self._stop.clear()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = Path("output/recordings") / ts
        session_dir.mkdir(parents=True, exist_ok=True)
        raw_path = session_dir / "raw.mp4"

        # Get first frame to define size
        first = None
        while first is None:
            first = frame_provider()
            time.sleep(0.005)
        h, w = first.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*self.shared.config.get("recording", {}).get("codec", "mp4v"))
        vw = cv2.VideoWriter(str(raw_path), fourcc, self.fps, (w, h))

        start = time.time()
        frame_count = 0
        thumb = None
        while not self._stop.is_set():
            now = time.time()
            if now - start >= duration_s:
                break
            frame = frame_provider()
            if frame is None:
                time.sleep(0.001)
                continue
            vw.write(frame)
            frame_count += 1
            if thumb is None:
                thumb = frame.copy()
            # pace to fps
            time.sleep(max(0, (frame_count / self.fps) - (now - start)))

        vw.release()
        self.is_recording = False

        # Save thumbnail
        if thumb is not None:
            cv2.imwrite(str(session_dir / "thumb.jpg"), thumb)

        # Metadata
        metadata = {
            "session_id": ts,
            "frames": frame_count,
            "fps": self.fps,
            "width": w,
            "height": h,
            "template_id": self.shared.get_param("postprocess.template_id"),
            "event_name": self.shared.get_param("postprocess.event_name"),
            "description": self.shared.get_param("postprocess.description"),
            "created_at": ts,
            "raw_path": str(raw_path),
        }
        with (session_dir / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Postprocess
        try:
            postprocess_recording(raw_path, metadata, self.shared)
        except Exception as e:
            print("Postprocess error:", e)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
