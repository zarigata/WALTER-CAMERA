@echo off
echo ==================================
echo Petrobras Camera Booth Setup
echo ==================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11 or 3.13 and try again.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

echo Removing old virtual environment...
if exist venv (
    rmdir /s /q venv
    echo Old venv removed.
) else (
    echo No existing venv found.
)
echo.

echo Clearing pip cache...
pip cache purge >nul 2>&1
echo Pip cache cleared.
echo.

echo Creating fresh virtual environment...
python -m venv venv

if not exist venv\Scripts\activate (
    echo ERROR: Failed to create virtual environment.
    echo Please check your Python installation.
    pause
    exit /b 1
)

echo Virtual environment created successfully!
echo.

echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ==================================
echo Installation completed successfully!
echo ==================================
echo.
echo You can now run 'run.bat' to start the application.
echo.
echo Tablet: http://localhost:8000/tablet
echo Admin:  http://localhost:8000/admin
echo Download: http://localhost:8000/download
echo.
pause
