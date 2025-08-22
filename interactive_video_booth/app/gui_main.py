from __future__ import annotations
import threading

from .config import load_config
from .pipeline import PipelineManager
from .ui.gui import AppGUI


def main():
    cfg = load_config('interactive_video_booth/app/config.yaml')
    # In GUI mode, disable OpenCV fullscreen windows
    try:
        cfg.render.fullscreen = False
    except Exception:
        pass

    pipeline = PipelineManager(cfg)

    def start_capture(duration_s: int):
        pipeline.countdown_and_record(duration_s=duration_s)

    def set_filter(name: str):
        pipeline.filter_used = name
        pipeline.renderer.effect = name

    gui = AppGUI(start_capture_cb=start_capture, set_filter_cb=set_filter)
    pipeline.set_frame_callback(gui.push_frame)

    gui.run()


if __name__ == "__main__":
    main()
