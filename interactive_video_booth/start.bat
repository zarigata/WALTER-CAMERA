@echo off
setlocal ENABLEDELAYEDEXPANSION
pushd %~dp0

REM Activate venv if present
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python -m interactive_video_booth.main --auto %*
set EXITCODE=%ERRORLEVEL%
popd
exit /b %EXITCODE%
