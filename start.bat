@echo off
echo ========================================
echo  Walter Camera - Start Application
echo ========================================
echo.

echo Checking if virtual environment exists...
if not exist "walter_camera_env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)
echo Virtual environment found.
echo.

echo Activating virtual environment...
call walter_camera_env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

echo Checking if main.py exists...
if not exist "main.py" (
    echo ERROR: main.py not found in current directory.
    pause
    exit /b 1
)
echo main.py found.
echo.

echo ========================================
echo Starting Walter Camera Application...
echo ========================================
echo.
echo Application will start multiple web servers:
echo - Main Control: http://localhost:5000
echo - Configuration: http://localhost:5001
echo - Macro Control: http://localhost:5002
echo - Tablet Control: http://localhost:5004
echo - Download Page: http://localhost:5003
echo.
echo Press Ctrl+C to stop the application.
echo.

python main.py

echo.
echo Application stopped.
echo.
pause
