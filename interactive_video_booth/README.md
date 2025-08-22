# Real-time Silhouette Capture Booth (Baseline)

This repository provides a modular, low-latency pipeline for real-time silhouette/outline rendering, countdown-driven recording to MP4 (H.264), thumbnail + JSON export, and a REST API to trigger captures. It is designed for GPU Linux deployment and supports Windows development.

## Features (Baseline)
- Live camera preview with resilient silhouettes (MOG2 + motion fusion + anti-blink persistence)
- Fullscreen rendering with glow and density effects (OpenCV-based; OpenGL planned)
- Countdown (3..2..1) + 10s recording (configurable)
- Atomic export: MP4 + thumbnail + JSON to watched folder
- REST API: POST /capture, GET /status/{job_id}, GET /list-outputs
- Modular design to plug in GPU segmenters (YOLOv8-seg, ONNX/TensorRT) later

## Requirements
- Python 3.10/3.11 (use system-installed Python)
- FFmpeg installed and in PATH (recommended for H.264). On Windows, download from ffmpeg.org.
- One or two UVC webcams, or RTSP sources

## Quick Start (Windows PowerShell and cmd compatible)
1. Create virtual environment
   - PowerShell: `python -m venv .venv` then `./.venv/Scripts/Activate.ps1`
   - cmd: `python -m venv .venv` then `.venv\Scripts\activate.bat`
2. Install deps
   - `python -m pip install --upgrade pip`
   - `pip install -r interactive_video_booth/requirements.txt`
3. Configure
   - Edit `interactive_video_booth/app/config.yaml` (camera IDs, fps, duration, watched folder)
4. Run API + preview
   - `python -m interactive_video_booth.app.main`
   - API at http://127.0.0.1:8000 (docs at `/docs`)

### Docker (GPU) — optional
If you prefer containerized deployment with NVIDIA GPU, let us know and we’ll add a Dockerfile + compose with `--gpus all`. All scripts will be provided in bash and cmd compatible form.

## End-to-End Test Capture
- Open docs: http://127.0.0.1:8000/docs
- POST `/capture` with `{ "duration": 10, "filter_id": "glow", "camera_ids": [0] }`
- Observe countdown on the fullscreen window
- After ~10s, files appear in `interactive_video_booth/outputs/` atomically:
  - `YYYYMMDD_HHMMSS_<jobid>_record.mp4`
  - `YYYYMMDD_HHMMSS_<jobid>_thumb.jpg`
  - `YYYYMMDD_HHMMSS_<jobid>.json`

## Roadmap
- GPU segmentation (YOLOv8-seg/ONNX/TensorRT)
- Multi-camera fusion (OR/weighted union) and re-id assignments
- OpenGL/WebGL renderer + Electron/React control UI with WebSocket previews
- Extensive tests and strobe/occlusion robustness cases
