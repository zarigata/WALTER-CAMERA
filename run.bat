@echo off
echo Starting the application...

if not exist venv\Scripts\activate (
    echo Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Launching server...
uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
