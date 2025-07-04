@echo off
setlocal

echo [INFO] RTMP Stream Setup - First Time Setup
echo.
echo This script will install Python dependencies and set up the environment.
echo.

REM Check admin privileges
net session >nul 2>&1
if NOT %errorLevel% == 0 (
    echo [WARNING] Administrator privileges recommended for best compatibility.
    echo If you encounter issues, try running as Administrator.
    echo.
)

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in the system PATH.
    echo.
    echo Please install Python 3.7+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found. Installing dependencies...
echo.

REM Install Python dependencies
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. 
    echo Please check your internet connection and try again.
    echo You can also manually install with: pip install rich pyperclip psutil
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Setup completed successfully!
echo.
echo NEXT STEPS:
echo 1. Connect your Android device via USB
echo 2. Enable USB Debugging on your device
echo 3. Run "launch_rtmp_setup.bat" to start the application
echo.
echo REQUIREMENTS:
echo - Android Debug Bridge (ADB) installed
echo - Android device with USB debugging enabled
echo - Streaming app installed on device (default: Telegram)
echo.
pause

endlocal