@echo off
setlocal

REM Check admin privileges
net session >nul 2>&1
if NOT %errorLevel% == 0 (
    echo This script requires Administrator privileges.
    echo Right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

echo [INFO] RTMP Stream Setup Launcher
echo.

REM Get the directory of the batch file
set BATCH_DIR=%~dp0

REM Set the path to the Python script (relative to batch file)
set SCRIPT_PATH="%BATCH_DIR%setupRTMP6.py"
set MONA_SERVER_DIR="%BATCH_DIR%MonaServer_Win64"
set MONA_SERVER_EXE_PATH="%BATCH_DIR%MonaServer_Win64\MonaServer.exe"

REM Check if MonaServer directory exists
if not exist %MONA_SERVER_DIR% (
    echo [ERROR] MonaServer_Win64 directory not found at %MONA_SERVER_DIR%
    echo Please ensure MonaServer_Win64 directory exists in the same location as this batch file.
    pause
    exit /b 1
)

REM Check if MonaServer.exe exists
if not exist %MONA_SERVER_EXE_PATH% (
    echo [ERROR] MonaServer.exe not found at %MONA_SERVER_EXE_PATH%
    echo Please ensure MonaServer.exe is in the MonaServer_Win64 directory.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in the system PATH.
    echo Please install Python 3.7+ or add it to the PATH.
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo [INFO] Checking Python dependencies...
python -c "import rich, pyperclip, psutil" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing required Python packages...
    pip install -r "%BATCH_DIR%requirements.txt"
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please run:
        echo pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM Try to activate conda environment if available
where conda >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Conda detected, activating base environment...
    call conda activate base >nul 2>&1
)

REM Run the Python script
echo [INFO] Starting RTMP Setup Assistant...
echo.
python %SCRIPT_PATH%

echo.
echo [INFO] The Python script has finished.
echo If MonaServer was started, it should still be running in the background.
echo You can stop MonaServer by finding its process or using Task Manager.
pause

endlocal