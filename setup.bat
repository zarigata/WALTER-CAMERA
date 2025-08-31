@echo off
echo ========================================
echo  Walter Camera - Setup Script
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)
echo Python is installed.
echo.

echo Cleaning up any existing virtual environment...
if exist "walter_camera_env" (
    echo Removing existing virtual environment...
    rmdir /s /q walter_camera_env
    if %errorlevel% neq 0 (
        echo WARNING: Could not remove existing virtual environment.
        echo Please delete the 'walter_camera_env' folder manually and try again.
        pause
        exit /b 1
    )
)
echo Cleaned up existing environment.
echo.

echo Creating virtual environment...
python -m venv walter_camera_env
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    echo Make sure you have write permissions in this directory.
    pause
    exit /b 1
)
echo Virtual environment created.
echo.

echo Activating virtual environment...
call "%~dp0walter_camera_env\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    echo Virtual environment may be corrupted.
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo WARNING: Failed to upgrade pip, continuing with installation...
)

echo Installing required packages...
pip install flask watchdog pyautogui obs-websocket-py
if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages.
    echo You may need to run this script as administrator or check your internet connection.
    pause
    exit /b 1
)
echo All packages installed successfully.
echo.

echo Creating necessary folders...
if not exist "videos" mkdir videos
if not exist "old_videos" mkdir old_videos
echo Folders created.
echo.

echo ========================================
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Make sure OBS Studio is installed and running
echo 2. Enable WebSocket server in OBS (Tools -> WebSocket Server Settings)
echo 3. Use start.bat to run the application
echo ========================================
echo.
pause
