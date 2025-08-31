@echo off
echo ========================================
echo  Walter Camera - Stop Application
echo ========================================
echo.

echo Looking for running Walter Camera processes...
echo.

REM Try to find and kill Python processes running main.py
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /nh ^| findstr /i "python.exe"') do (
    REM Get the command line for each Python process
    for /f "tokens=*" %%a in ('wmic process where "processid=%%i" get commandline /value ^| findstr /i "main.py"') do (
        echo Found Walter Camera process (PID: %%i)
        echo Stopping process...
        taskkill /pid %%i /t /f >nul 2>&1
        if %errorlevel% equ 0 (
            echo Process stopped successfully.
        ) else (
            echo Failed to stop process.
        )
        goto :found
    )
)

REM If no main.py process found, try to kill any python.exe running from this directory
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /nh ^| findstr /i "python.exe"') do (
    for /f "tokens=*" %%a in ('wmic process where "processid=%%i" get executablepath /value') do (
        echo %%a | findstr /i "walter camera" >nul 2>&1
        if %errorlevel% equ 0 (
            echo Found Python process in Walter Camera directory (PID: %%i)
            echo Stopping process...
            taskkill /pid %%i /t /f >nul 2>&1
            if %errorlevel% equ 0 (
                echo Process stopped successfully.
            ) else (
                echo Failed to stop process.
            )
            goto :found
        )
    )
)

echo No running Walter Camera processes found.
echo The application may not be running.
goto :end

:found
echo.
echo Attempting to stop any remaining Flask server processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Walter Camera*" >nul 2>&1
taskkill /f /im python.exe /fi "IMAGENAME eq python.exe" /fi "CPUTIME gt 00:00:01" >nul 2>&1

:end
echo.
echo ========================================
echo Stop operation completed.
echo ========================================
echo.
pause
