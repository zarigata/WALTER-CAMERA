import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from app.config.schema import SharedState


def which(program):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        fp = Path(p) / program
        if fp.exists():
            return str(fp)
    return None


def ffmpeg_available():
    return which("ffmpeg.exe") or which("ffmpeg")


def postprocess_recording(raw_path: Path, metadata: Dict, shared: SharedState):
    raw_path = Path(raw_path)
    session_id = metadata.get("session_id")
    out_base = Path("output/ksusesender_ready") / session_id
    out_base.mkdir(parents=True, exist_ok=True)

    overlay = shared.config.get("postprocess", {}).get("overlay_path")
    overlay = Path(overlay) if overlay else None
    final_video = out_base / f"{session_id}.mp4"

    if overlay and overlay.exists() and ffmpeg_available():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_path),
            "-i", str(overlay),
            "-filter_complex", "[0:v][1:v]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)",
            "-c:a", "copy",
            str(final_video),
        ]
        subprocess.run(cmd, check=False)
    else:
        # Fallback: copy raw
        shutil.copy2(raw_path, final_video)

    # ksuseSender metadata JSON
    ksuse_meta = {
        "template_id": metadata.get("template_id"),
        "event_name": metadata.get("event_name"),
        "description": metadata.get("description"),
        "video_path": str(final_video.resolve()),
        "session_id": session_id,
    }
    with (out_base / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(ksuse_meta, f, ensure_ascii=False, indent=2)
