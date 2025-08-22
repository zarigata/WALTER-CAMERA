from __future__ import annotations
import threading
import time
import uuid
from typing import Optional

import cv2
import numpy as np

from .config import Config
from .capture.camera import CameraStream
from .detection.segmentation import Segmenter
from .fusion.fuser import MaskFuser
from .tracking.tracker import SimpleTracker
from .render.renderer import Renderer
from .recording.recorder import Recorder
from .utils.logging import setup_logging


class PipelineManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = setup_logging()
        self.cam = CameraStream(cfg.cameras.primary_camera_id, cfg.app.fps, cfg.app.output_width, cfg.app.output_height).start()
        self.segmenter = Segmenter()
        self.fuser = MaskFuser(cfg.fusion.seg_weight, cfg.fusion.motion_weight, cfg.fusion.on_threshold, cfg.fusion.off_threshold, cfg.fusion.persistence_frames)
        self.tracker = SimpleTracker(cfg.fusion.persistence_frames)
        self.renderer = Renderer(cfg.app.output_width, cfg.app.output_height, cfg.render.fullscreen, cfg.render.window_name, cfg.render.effect)
        self.recorder: Optional[Recorder] = None
        self.recording = False
        self.record_lock = threading.Lock()
        self.job_id: Optional[str] = None
        self.person_count = 0
        self.filter_used = cfg.render.effect
        # GUI integration
        self.gui_mode = False
        self._frame_cb = None  # type: Optional[callable]
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        last_preview = 0
        while True:
            frame = self.cam.read()
            if frame is None:
                time.sleep(0.01)
                continue
            mask_raw, conf = self.segmenter.apply(frame)
            fused = self.fuser.fuse(frame, mask_raw, conf)
            tracked = self.tracker.update(fused)
            self.person_count = 1 if np.count_nonzero(tracked) > 0 else 0

            # Render or push to GUI
            if self.gui_mode and self._frame_cb:
                composed = self.renderer.compose_frame(frame, tracked)
                try:
                    self._frame_cb(composed)
                except Exception:
                    pass
            else:
                self.renderer.render(frame, tracked)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC to exit display only
                    break

            # Recording
            if self.recording and self.recorder is not None:
                self.recorder.write(cv2.resize(frame, (self.cfg.app.output_width, self.cfg.app.output_height)))

    def countdown_and_record(self, duration_s: int | None = None, job_id: str | None = None) -> dict:
        dur = int(duration_s or self.cfg.app.record_duration_s)
        with self.record_lock:
            if self.recording:
                return {"status": "busy"}
            self.job_id = job_id or uuid.uuid4().hex[:8]
            self.recording = True
        # Countdown overlay
        for t in [3, 2, 1]:
            frame = self.cam.read()
            if frame is None:
                time.sleep(0.1)
                continue
            overlay = cv2.resize(frame.copy(), (self.cfg.app.output_width, self.cfg.app.output_height))
            cv2.putText(overlay, str(t), (int(0.45 * overlay.shape[1]), int(0.55 * overlay.shape[0])), cv2.FONT_HERSHEY_SIMPLEX, 6, (0, 0, 255), 12, cv2.LINE_AA)
            if self.gui_mode and self._frame_cb:
                try:
                    self._frame_cb(overlay)
                except Exception:
                    pass
            else:
                cv2.imshow(self.cfg.render.window_name, overlay)
                cv2.waitKey(1)
            time.sleep(1.0)

        # Start recorder
        self.recorder = Recorder(self.cfg.app.watched_folder, self.cfg.app.output_width, self.cfg.app.output_height, self.cfg.app.fps)
        final_path = self.recorder.start(self.job_id)
        start = time.time()
        first_frame = None
        last_frame = None
        while time.time() - start < dur:
            frame = self.cam.read()
            if frame is None:
                time.sleep(0.005)
                continue
            frame_resized = cv2.resize(frame, (self.cfg.app.output_width, self.cfg.app.output_height))
            if first_frame is None:
                first_frame = frame_resized.copy()
            last_frame = frame_resized.copy()
            self.recorder.write(frame_resized)
            cv2.waitKey(1)
        self.recorder.stop()
        self.recording = False
        thumb, meta = self.recorder.export_sidecars(
            final_video_path=final_path,
            job_id=self.job_id,
            first_frame_bgr=first_frame if first_frame is not None else last_frame,
            last_frame_bgr=last_frame if last_frame is not None else first_frame,
            duration_s=dur,
            fps=self.cfg.app.fps,
            camera_ids=[self.cfg.cameras.primary_camera_id],
            person_count=self.person_count,
            filter_used=self.filter_used,
        )
        return {"status": "ok", "job_id": self.job_id, "video": final_path, "thumb": thumb, "meta": meta}

    def stop(self):
        self.cam.stop()
        self.renderer.close()

    # GUI bridge
    def set_frame_callback(self, cb):
        self._frame_cb = cb
        self.gui_mode = cb is not None
