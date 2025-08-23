@echo off
setlocal enableextensions
pushd %~dp0\..

REM 1) Create venv and install requirements
call install.bat
if errorlevel 1 goto :error

REM Activate venv for the rest of the steps
call .venv\Scripts\activate.bat

REM 2) Stage 0 to generate runtime_backend.json (auto backend selection)
python -m interactive_video_booth.main --stage 0 --inference auto
if errorlevel 1 goto :error

REM 3) Download models (one-time online)
python -m interactive_video_booth.main --prepare-models
if errorlevel 1 goto :error

REM 4) Snapshot environment and lock dependencies
python -m interactive_video_booth.main --snapshot-env
if errorlevel 1 goto :error

REM 5) Run smoke tests
call run_smoke_tests.bat
if errorlevel 1 goto :error

popd

echo Bootstrap completed successfully.
exit /b 0

:error
popd
echo Bootstrap failed. Check logs for details.
exit /b 1
