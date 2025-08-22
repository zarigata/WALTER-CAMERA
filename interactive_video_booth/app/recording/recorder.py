from __future__ import annotations
import os
import json
import time
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Optional

import cv2
import numpy as np
from PIL import Image


class Recorder:
    def __init__(self, out_dir: str, width: int, height: int, fps: int):
        self.out_dir = out_dir
        self.w = width
        self.h = height
        self.fps = fps
        self.proc: Optional[subprocess.Popen] = None
        self.temp_path = None
        self.final_path = None
        os.makedirs(self.out_dir, exist_ok=True)

    def _has_ffmpeg(self) -> bool:
        from shutil import which
        return which('ffmpeg') is not None

    def start(self, job_id: str):
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        base = f"{ts}_{job_id}"
        self.final_path = os.path.join(self.out_dir, f"{base}_record.mp4")
        self.temp_path = self.final_path + ".tmp"

        if self._has_ffmpeg():
            cmd = [
                'ffmpeg', '-y',
                '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{self.w}x{self.h}', '-r', str(self.fps), '-i', '-',
                '-an', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'veryfast', '-crf', '20', self.temp_path
            ]
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        else:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.proc = None
            self.vw = cv2.VideoWriter(self.temp_path, fourcc, self.fps, (self.w, self.h))

        return self.final_path

    def write(self, frame_bgr: np.ndarray):
        if self.proc is not None and self.proc.stdin:
            self.proc.stdin.write(frame_bgr.tobytes())
        else:
            self.vw.write(frame_bgr)

    def stop(self):
        if self.proc is not None:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait()
            self.proc = None
        else:
            self.vw.release()
        # Atomic rename
        if self.temp_path and self.final_path:
            os.replace(self.temp_path, self.final_path)
        return self.final_path

    def export_sidecars(self, final_video_path: str, job_id: str, first_frame_bgr: np.ndarray, last_frame_bgr: np.ndarray, duration_s: int, fps: int, camera_ids: list[int], person_count: int, filter_used: str):
        ts = os.path.basename(final_video_path).split('_')[0]
        base_no_suffix = os.path.basename(final_video_path).replace('_record.mp4', '')
        thumb_path = os.path.join(self.out_dir, f"{base_no_suffix}_thumb.jpg")
        thumb_tmp = thumb_path + '.tmp'
        meta_path = os.path.join(self.out_dir, f"{base_no_suffix}.json")

        # Thumbnail from mid-frame approximation
        mid = cv2.resize(last_frame_bgr, (300, 169))
        Image.fromarray(cv2.cvtColor(mid, cv2.COLOR_BGR2RGB)).save(thumb_tmp, quality=90)
        os.replace(thumb_tmp, thumb_path)

        meta = {
            "filename": os.path.basename(final_video_path),
            "timestamp_utc": ts,
            "duration_s": duration_s,
            "fps": fps,
            "camera_ids": camera_ids,
            "person_count": person_count,
            "filter_used": filter_used,
        }
        with open(meta_path + '.tmp', 'w', encoding='utf-8') as f:
            json.dump(meta, f)
        os.replace(meta_path + '.tmp', meta_path)
        return thumb_path, meta_path
