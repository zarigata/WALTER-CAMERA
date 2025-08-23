@echo off
setlocal enableextensions

REM Prepare models online (one-time) so future runs are fully offline.
REM Works in CMD and PowerShell.

REM Ensure venv is activated before running, or python resolves to system Python with required deps.
python -m interactive_video_booth.main --prepare-models

if errorlevel 1 (
  echo Failed to prepare models. See logs for details.
  exit /b 1
)

echo Models prepared successfully.
exit /b 0
