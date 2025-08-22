# Interactive LED Photo-Booth

A cross-platform Python app for a real-time "aura" effect photo/video booth with remote sliders, recording, postprocess overlays, and ksuseSender-ready outputs.

## Features
- Real-time capture (USB/RTSP) with OpenCV.
- Dynamic, adjustable effects (aura, trails, skeleton placeholder).
- Remote slider controls over WebSocket (LAN).
- Countdown trigger, record N seconds, save MP4 + JSON metadata + thumbnail.
- Postprocess via FFmpeg overlays and ksuseSender-ready JSON.
- Graceful fallbacks if GPU/segmentation model unavailable.

## Quick Start (Non-Docker)
1. Create and activate a virtual environment (Windows PowerShell or cmd):
```
python -m venv .venv
.\.venv\Scripts\activate
```
2. Install deps:
```
pip install -r requirements.txt
```
3. Run the app:
```
python -m app.main
```

Controls:
- Open the slider UI from another LAN PC: open `app/remote_api/static/sliders.html`, set `WS_URL` to your host: `ws://<HOST_IP>:8765`.
- Press `R` on the display window or use the slider UI "Record" button to start a countdown and record.
- Press `Q` to quit.

## Docker (Optional)
You can run this in Docker if desired (provide host camera and GPU passthrough as needed). See `Dockerfile` for a base image.

## Output
- Raw recordings: `./output/recordings/<session_id>/raw.mp4`
- Postprocessed + metadata: `./output/ksusesender_ready/<session_id>/`

## Configuration
See `app/config/settings.yaml` for defaults. Hot parameters can be adjusted at runtime over WebSocket.

## Tests
```
python -m pytest -q
```

## Notes
- FFmpeg must be installed and on PATH for postprocessing overlays.
- LAN only by default.
