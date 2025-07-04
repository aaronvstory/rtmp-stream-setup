@echo off
setlocal EnableDelayedExpansion

echo ================================================================
echo       RTMP Stream Setup Assistant - Complete Installation
echo ================================================================
echo.
echo This setup will automatically install all dependencies and 
echo configure your system for RTMP streaming from Android devices.
echo.

REM Check admin privileges
net session >nul 2>&1
if NOT %errorLevel% == 0 (
    echo [WARNING] Administrator privileges recommended for automatic installations.
    echo If automatic installations fail, you may need to run as Administrator.
    echo.
    echo Press any key to continue with current privileges...
    pause >nul
    echo.
)

REM =================================================================
REM                    PYTHON DEPENDENCY CHECK
REM =================================================================
echo [STEP 1/4] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in the system PATH.
    echo.
    echo Please install Python 3.7+ from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    echo After installing Python, re-run this setup script.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] Found: %%i
)

echo [INFO] Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    echo Trying alternative installation method...
    pip install rich pyperclip psutil
    if %errorLevel% neq 0 (
        echo [ERROR] Could not install required packages.
        echo Please check your internet connection and Python installation.
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies installed successfully.
echo.
REM =================================================================
REM                 ANDROID DEBUG BRIDGE (ADB) CHECK
REM =================================================================
echo [STEP 2/4] Checking Android Debug Bridge (ADB)...

REM Check if ADB is in PATH
adb version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('adb version 2^>^&1 ^| findstr "Android Debug Bridge"') do echo [OK] Found: %%i
    set ADB_FOUND=1
    goto :adb_done
)

REM Check common ADB locations
set ADB_FOUND=0
if exist "C:\platform-tools\adb.exe" (
    echo [OK] Found ADB at: C:\platform-tools\adb.exe
    set ADB_FOUND=1
    goto :adb_done
)

if exist "C:\Android\platform-tools\adb.exe" (
    echo [OK] Found ADB at: C:\Android\platform-tools\adb.exe
    set ADB_FOUND=1
    goto :adb_done
)

REM ADB not found - offer installation
echo [INFO] Android Debug Bridge (ADB) not found.
echo.
echo ADB is required for communicating with Android devices.
echo.
echo OPTIONS:
echo [1] Download and install ADB automatically (Recommended)
echo [2] I have ADB installed elsewhere (Browse to location)
echo [3] Skip ADB setup (configure manually later)
echo.
set /p ADB_CHOICE="Enter your choice (1-3): "

if "%ADB_CHOICE%"=="1" goto :install_adb
if "%ADB_CHOICE%"=="2" goto :browse_adb
if "%ADB_CHOICE%"=="3" goto :skip_adb

echo [ERROR] Invalid choice. Please enter 1, 2, or 3.
goto :adb_not_found

:install_adb
echo [INFO] Downloading Android Platform Tools...
echo This may take a few minutes depending on your internet connection.

REM Create directory
if not exist "C:\platform-tools" mkdir "C:\platform-tools"

REM Download platform-tools
echo [INFO] Downloading from Google servers...
curl -L -o "C:\platform-tools.zip" "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to download ADB. Please check internet connection.
    echo You can manually download from: https://developer.android.com/studio/releases/platform-tools
    goto :browse_adb
)

REM Extract files
echo [INFO] Extracting Android Platform Tools...
powershell -command "Expand-Archive -Path 'C:\platform-tools.zip' -DestinationPath 'C:\' -Force" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to extract ADB files.
    del "C:\platform-tools.zip" 2>nul
    goto :browse_adb
)

REM Cleanup
del "C:\platform-tools.zip" >nul 2>&1

REM Verify installation
if exist "C:\platform-tools\adb.exe" (
    echo [OK] ADB installed successfully at: C:\platform-tools\adb.exe
    set ADB_FOUND=1
) else (
    echo [ERROR] ADB installation failed.
    goto :browse_adb
)
goto :adb_done
:browse_adb
echo [INFO] Please select your ADB installation folder.
echo Look for the folder containing 'adb.exe' file.
echo.
pause

REM Use PowerShell folder browser
for /f "delims=" %%i in ('powershell -command "Add-Type -AssemblyName System.Windows.Forms; $folder = New-Object System.Windows.Forms.FolderBrowserDialog; $folder.Description = 'Select folder containing adb.exe'; $folder.ShowNewFolderButton = $false; if($folder.ShowDialog() -eq 'OK') { $folder.SelectedPath }"') do set "SELECTED_ADB_PATH=%%i"

if "!SELECTED_ADB_PATH!"=="" (
    echo [INFO] No folder selected. Skipping ADB setup.
    goto :skip_adb
)

if exist "!SELECTED_ADB_PATH!\adb.exe" (
    echo [OK] Found ADB at: !SELECTED_ADB_PATH!\adb.exe
    set ADB_FOUND=1
) else (
    echo [ERROR] adb.exe not found in selected folder: !SELECTED_ADB_PATH!
    echo.
    set /p RETRY_ADB="Try selecting another folder? (y/n): "
    if /i "!RETRY_ADB!"=="y" goto :browse_adb
    goto :skip_adb
)
goto :adb_done

:skip_adb
echo [WARNING] ADB setup skipped. You will need to configure ADB path manually.
echo You can configure it later when running the application.
set ADB_FOUND=0

:adb_done
echo.

REM =================================================================
REM                    MONASERVER CHECK
REM =================================================================
echo [STEP 3/4] Checking MonaServer (RTMP Server)...

REM Check if MonaServer exists in project directory
if exist "MonaServer_Win64\MonaServer.exe" (
    echo [OK] Found MonaServer at: MonaServer_Win64\MonaServer.exe
    set MONA_FOUND=1
    goto :mona_done
)

echo [INFO] MonaServer not found in project directory.
echo.
echo MonaServer is the RTMP streaming server component.
echo It should be included with this project.
echo.
echo OPTIONS:
echo [1] The MonaServer files should be here - check project integrity
echo [2] I have MonaServer installed elsewhere (Browse to location)
echo [3] Skip MonaServer setup (configure manually later)
echo.
set /p MONA_CHOICE="Enter your choice (1-3): "

if "%MONA_CHOICE%"=="1" goto :check_project
if "%MONA_CHOICE%"=="2" goto :browse_mona
if "%MONA_CHOICE%"=="3" goto :skip_mona

echo [ERROR] Invalid choice. Please enter 1, 2, or 3.
goto :mona_not_found

:check_project
echo [INFO] Checking project integrity...
if exist "setupRTMP6.py" (
    echo [WARNING] MonaServer_Win64 directory is missing from project.
    echo This suggests an incomplete download or extraction.
    echo.
    echo Please re-download the complete project from:
    echo https://github.com/aaronvstory/rtmp-stream-setup
    echo.
    echo Or select a MonaServer installation manually.
    goto :browse_mona
) else (
    echo [ERROR] Project files missing. Please re-download the complete project.
    goto :skip_mona
)

:browse_mona
echo [INFO] Please select your MonaServer executable file.
echo Look for 'MonaServer.exe' file.
echo.
pause

REM Use PowerShell file browser for MonaServer.exe
for /f "delims=" %%i in ('powershell -command "Add-Type -AssemblyName System.Windows.Forms; $file = New-Object System.Windows.Forms.OpenFileDialog; $file.Filter = 'MonaServer Executable (MonaServer.exe)|MonaServer.exe|All Files (*.*)|*.*'; $file.Title = 'Select MonaServer.exe'; if($file.ShowDialog() -eq 'OK') { $file.FileName }"') do set "SELECTED_MONA_PATH=%%i"

if "!SELECTED_MONA_PATH!"=="" (
    echo [INFO] No file selected. Skipping MonaServer setup.
    goto :skip_mona
)

if exist "!SELECTED_MONA_PATH!" (
    echo [OK] Found MonaServer at: !SELECTED_MONA_PATH!
    set MONA_FOUND=1
) else (
    echo [ERROR] Selected MonaServer file not accessible.
    set /p RETRY_MONA="Try selecting another file? (y/n): "
    if /i "!RETRY_MONA!"=="y" goto :browse_mona
    goto :skip_mona
)
goto :mona_done

:skip_mona
echo [WARNING] MonaServer setup skipped. You will need to configure MonaServer path manually.
echo You can configure it later when running the application.
set MONA_FOUND=0

:mona_done
echo.
REM =================================================================
REM                      CONFIGURATION UPDATE
REM =================================================================
echo [STEP 4/4] Updating configuration...

REM Update config.ini with found paths
if %ADB_FOUND%==1 (
    if defined SELECTED_ADB_PATH (
        echo [INFO] Updating ADB path in configuration: !SELECTED_ADB_PATH!\adb.exe
        powershell -command "(Get-Content config.ini) -replace '^adbpath = .*', 'adbpath = !SELECTED_ADB_PATH!\adb.exe' | Set-Content config.ini"
    ) else if exist "C:\platform-tools\adb.exe" (
        echo [INFO] Updating ADB path in configuration: C:\platform-tools\adb.exe
        powershell -command "(Get-Content config.ini) -replace '^adbpath = .*', 'adbpath = C:\platform-tools\adb.exe' | Set-Content config.ini"
    )
)

if %MONA_FOUND%==1 (
    if defined SELECTED_MONA_PATH (
        echo [INFO] Updating MonaServer path in configuration: !SELECTED_MONA_PATH!
        powershell -command "(Get-Content config.ini) -replace '^monaserverpath = .*', 'monaserverpath = !SELECTED_MONA_PATH!' | Set-Content config.ini"
    ) else if exist "MonaServer_Win64\MonaServer.exe" (
        echo [INFO] Using bundled MonaServer configuration
        powershell -command "(Get-Content config.ini) -replace '^monaserverpath = .*', 'monaserverpath = .\MonaServer_Win64\MonaServer.exe' | Set-Content config.ini"
    )
)

echo [OK] Configuration updated.
echo.

REM =================================================================
REM                      SETUP COMPLETION
REM =================================================================
echo ================================================================
echo                      SETUP COMPLETED!
echo ================================================================
echo.

if %ADB_FOUND%==1 if %MONA_FOUND%==1 (
    echo [SUCCESS] All components installed and configured successfully!
    echo.
    echo READY TO USE:
    echo   [OK] Python and dependencies
    echo   [OK] Android Debug Bridge (ADB)
    echo   [OK] MonaServer (RTMP Server)
    echo.
    echo NEXT STEPS:
    echo 1. Connect your Android device via USB
    echo 2. Enable USB Debugging in Developer Options
    echo 3. Run 'launch_rtmp_setup.bat' to start streaming
    echo.
) else (
    echo [PARTIAL] Setup completed with some manual configuration needed:
    echo.
    if %ADB_FOUND%==0 echo   [!] ADB needs manual configuration
    if %MONA_FOUND%==0 echo   [!] MonaServer needs manual configuration
    echo.
    echo The application will guide you through configuring missing components
    echo when you first run 'launch_rtmp_setup.bat'.
    echo.
)

echo ================================================================
echo                    IMPORTANT INFORMATION
echo ================================================================
echo.
echo RTMP STREAMING URL:
echo   Default: rtmp://127.0.0.1:1935/live
echo   This URL is automatically copied to your clipboard when streaming starts.
echo.
echo CUSTOM STREAM NAMES:
echo   To use custom stream names, append to the URL:
echo   rtmp://127.0.0.1:1935/live/YOUR_CUSTOM_NAME
echo   Example: rtmp://127.0.0.1:1935/live/mystream
echo.
echo CONNECTION METHODS SUPPORTED:
echo   [USB] Connect device via USB cable (most reliable)
echo   [WiFi] Connect via ADB over WiFi (requires initial USB setup)
echo.
echo WiFi SETUP (Optional):
echo   1. Connect device via USB first
echo   2. Run: adb tcpip 5555
echo   3. Find device IP: adb shell ip addr show wlan0
echo   4. Connect: adb connect DEVICE_IP:5555
echo   5. Disconnect USB cable
echo.
echo STREAMING APPS:
echo   Default: Telegram (configured in config.ini)
echo   Works with any RTMP-capable mobile streaming app
echo   You can change the app in config.ini [Device] packagename setting
echo.
echo TROUBLESHOOTING:
echo   - Ensure USB Debugging is enabled on Android device
echo   - Accept USB debugging prompt when device connects
echo   - Check Windows Firewall settings for port 1935
echo   - Run as Administrator if port conflicts occur
echo.
echo For detailed documentation, see README.md
echo.

echo Press any key to finish setup...
pause >nul

echo.
echo [INFO] Setup complete! You can now run 'launch_rtmp_setup.bat'
echo.

endlocal