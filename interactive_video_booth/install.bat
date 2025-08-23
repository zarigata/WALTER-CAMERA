@echo off
REM Create venv and install requirements (Windows cmd-compatible)
setlocal
pushd %~dp0

if not exist .venv (
  echo Creating virtual environment in .venv ...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

popd
