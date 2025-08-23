@echo off
setlocal ENABLEDELAYEDEXPANSION
pushd %~dp0\..

if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
python -m interactive_video_booth.main --inference cpu --auto %*
set EXITCODE=%ERRORLEVEL%
popd
exit /b %EXITCODE%
