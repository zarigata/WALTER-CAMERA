import argparse
import asyncio
import os
import signal
import sys
import threading
import time
from pathlib import Path

import cv2

from app.config.schema import load_config, SharedState
from app.capture.camera import Camera
from app.processor.pipeline import ProcessingPipeline
from app.display.display import Display
from app.recorder.recorder import Recorder
from app.remote_api.websocket_server import run_websocket_server


def ensure_dirs():
    Path("output/recordings").mkdir(parents=True, exist_ok=True)
    Path("output/ksusesender_ready").mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Interactive LED Photo-Booth")
    parser.add_argument("--config", type=str, default="app/config/settings.yaml")
    parser.add_argument("--source", type=str, default="0", help="Camera index or RTSP URL")
    args = parser.parse_args()

    ensure_dirs()

    cfg = load_config(args.config)
    shared = SharedState(cfg)

    # Camera
    cam_source = 0 if args.source == "0" else args.source
    camera = Camera(cam_source, width=cfg.get("capture", {}).get("width", 1280), height=cfg.get("capture", {}).get("height", 720), fps=cfg.get("capture", {}).get("fps", 30))
    camera.start()

    # Processing pipeline
    pipeline = ProcessingPipeline(shared)

    # Display
    display = Display(window_name="BoothDisplay", fullscreen=True)

    # Recorder
    recorder = Recorder(shared, fps=camera.fps)

    # WebSocket server in background
    ws_thread = threading.Thread(target=run_websocket_server, args=(shared,), daemon=True)
    ws_thread.start()

    print("App started. Press R to record, Q to quit.")

    try:
        prev_time = time.time()
        while True:
            frame = camera.read()
            if frame is None:
                # Sleep briefly to avoid busy spin
                time.sleep(0.005)
                continue

            # Process
            frame_proc = pipeline.process(frame)

            # Draw countdown overlay if active
            if shared.countdown_active:
                remaining = max(0, int(shared.countdown_end_time - time.time()) + 1)
                cv2.putText(frame_proc, f"{remaining}", (frame_proc.shape[1]//2 - 20, frame_proc.shape[0]//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8, cv2.LINE_AA)

            # Display
            display.show(frame_proc)

            # Handle recording
            if shared.record_request and not recorder.is_recording:
                shared.record_request = False
                duration = int(shared.params.get("recording.duration_s", 10))
                # Start countdown on-screen, then recorder starts automatically
                shared.start_countdown(3)
                recorder.start_after_countdown(duration, lambda: pipeline.last_frame)

            # Quit handling
            key = display.poll_key()
            if key == ord('q') or key == ord('Q'):
                break
            if key == ord('r') or key == ord('R'):
                # Manual record trigger
                duration = int(shared.params.get("recording.duration_s", 10))
                shared.start_countdown(3)
                recorder.start_after_countdown(duration, lambda: pipeline.last_frame)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        display.close()
        camera.stop()
        recorder.stop()


if __name__ == "__main__":
    main()
