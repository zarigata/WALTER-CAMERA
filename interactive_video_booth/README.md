# Interactive Video Booth (Staged Build)

This repository contains a staged, self-testing prototype for a real-time camera system.

Implemented now:
- Stage 0 — Environment & prerequisites check
- Stage 1 — Camera discovery & validation
- Stage 2 — Model loading & single-frame inference (offline, ONNX Runtime with OpenCV DNN fallback)

Next iterations will add Stages 3–6 (pipeline, GUI, robustness, deployment).

## Requirements
- Python 3.9+ (uses system-installed Python; recommended 3.11 on Windows)
- Windows/macOS/Linux
- Camera device or RTSP URL (for Stage 1)

## Setup (Windows recommended)
1. Create and activate a virtual environment, then install deps:
   - PowerShell:
     ```powershell
     .\install.ps1
     ```
   - CMD:
     ```cmd
     install.bat
     ```
   - Or manually:
     ```powershell
     python -m venv .venv
     . .\.venv\Scripts\Activate.ps1
     pip install -r requirements.txt
     ```

2. Run smoke tests for Stage 0 and 1:
   - PowerShell/CMD:
     ```cmd
     run_smoke_tests.bat
     ```
   - Bash (Git Bash/WSL/macOS/Linux):
     ```bash
     ./run_smoke_tests.sh
     ```

3. Run the staged runner:
   - Full auto for implemented stages:
     ```powershell
     .\start.bat
     ```
   - Or run a specific stage:
     ```powershell
     python -m interactive_video_booth.main --stage 0
     python -m interactive_video_booth.main --stage 1 --device 0
     ```

## Stage 0 — Validation
- Verifies Python>=3.9.
- Verifies required packages are importable.
- Reports GPU availability (PyTorch CUDA or ONNX Runtime providers).
- Ensures directories: `logs/`, `configs/`, `models/`, `outputs/` are writable.
- On failure: writes `logs/stage0_error.log` and exits with codes:
  - 2: Python too old
  - 3: Missing packages / ONNXRuntime CPU provider missing
  - 4: Directory not writable

Example console output:
```
[STAGE 0] Python 3.11 detected
[STAGE 0] Missing packages: none
[STAGE 0] GPU: CUDA available
[STAGE 0] Directories created: logs/, configs/, models/, outputs/
```
If GPU absent, you will see: `WARNING: GPU not available. Proceeding in CPU-only mode; expect lower FPS.`

## CPU/GPU modes

You can pick the inference path without changing code:

- `--inference auto` (default): tries CUDA > DirectML > OpenVINO > CPU.
- `--inference gpu`: forces a GPU-first choice (CUDA or DirectML, then OpenVINO, then CPU).
- `--inference cpu`: prefers CPU-only; if OpenVINO EP is present it will be used, else plain CPU EP.

Quick launch scripts:

- Windows (CMD/PowerShell):
  ```cmd
  scripts\run_cpu.bat
  scripts\run_gpu.bat
  ```
- Bash:
  ```bash
  ./scripts/run_cpu.sh
  ./scripts/run_gpu.sh
  ```

Selected backend is written to `configs/runtime_backend.json`.

Notes:

- CUDA requires `onnxruntime-gpu` and NVIDIA drivers/CUDA runtime.
- DirectML (Windows, non-NVIDIA GPUs) requires `onnxruntime-directml`.
- OpenVINO EP (often fastest on Intel CPUs) requires installing Intel OpenVINO and initializing its env.

References:

- ONNX Runtime OpenVINO EP: https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html
- Ultralytics + OpenVINO integration: https://docs.ultralytics.com/integrations/openvino/

## Offline-first workflow

The system is designed to run entirely offline after a one-time online preparation step.

- **Step 1 (online, one-time):** prepare and validate models
  - PowerShell/CMD:
    ```cmd
    scripts\prepare_models.bat
    ```
  - Bash:
    ```bash
    ./scripts/prepare_models.sh
    ```
  - Or directly:
    ```bash
    python -m interactive_video_booth.main --prepare-models
    ```

  This downloads required assets into `models/` using an optional manifest `configs/models_manifest.json`.
  If the manifest is missing, a default entry for `yolov8n.onnx` is used.

- **Step 2 (offline, repeatable):** run stages normally
  - Examples:
    ```cmd
    python -m interactive_video_booth.main --auto --inference cpu --force
    python -m interactive_video_booth.main --stage 2 --inference auto --force
    ```

Notes:
- Stage 2 never downloads at runtime. It validates presence of required models locally; if missing, it fails fast unless `--force` is used (in which case it proceeds with diagnostics and saves outputs without inference).
- A default manifest is embedded; you may provide your own at `configs/models_manifest.json` to pin versions and hashes.

## Stage 1 — Camera discovery & validation
- Tries sources in order:
  - USB indices `0..4` (plus `--device` if supplied)
  - URLs from `configs/camera_sources.json`
- For each opened source, captures up to 60 frames or 3 seconds and checks `>=80%` frames are valid.
- Estimates FPS and resolution and probes supported controls where possible.
- Writes `logs/camera_report.json` and `configs/last_camera.json`.
- On success prints a one-line summary similar to:
```
[STAGE 1] Camera found: index=0 resolution=1280x720 fps=30 frames_ok_pct=100 controls_supported=['exposure']
```
- If only flaky sources are found, use `--force` to continue; GUI will later warn `camera_mode: flaky`.
- On failure: writes `logs/stage1_failure_report.txt` and exits with code 10.

Example config file `configs/camera_sources.json`:
```json
{
  "preferred": ["usb:0", "usb:1", "rtsp://192.168.1.100:8554/live"],
  "fallbacks": ["usb:2", "/dev/video0"]
}
```

## Troubleshooting
- You cannot change physical lens aperture via OpenCV. Only exposure/gain/etc. may be supported, depending on the camera and driver.
- If `onnxruntime` import fails, re-run `pip install -r requirements.txt` inside the virtual environment.
- If Stage 1 fails: ensure a camera is connected and not locked by other apps; try `--device 0` or an RTSP URL.

## Roadmap (coming next)
- Stage 2: Model download/load, single-frame inference, effects load
- Stage 3: Threaded pipeline, tracker integration, 10s sample output
- Stage 4: Second-screen GUI (PyQt6), live param tuning, self-test
- Stage 5: Health monitoring & auto-recovery
- Stage 6: Performance tuning & deploy scripts
