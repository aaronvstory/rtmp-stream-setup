# RTMP Stream Setup Assistant

A comprehensive tool for setting up RTMP streaming from Android devices with a beautiful terminal interface. This application automatically configures port forwarding, manages MonaServer, and provides a seamless streaming experience over **USB or WiFi connections**.

## ✨ Features

- **🎯 Automatic Setup**: One-click RTMP streaming configuration
- **📱 Device Detection**: Auto-detects connected Android devices (USB & WiFi)
- **🔄 Port Management**: Handles port conflicts and forwarding automatically  
- **🎨 Rich UI**: Beautiful terminal interface with progress bars and status updates
- **⚙️ MonaServer Integration**: Built-in RTMP server with optimized configuration
- **📋 Clipboard Support**: Automatically copies RTMP URLs to clipboard
- **🔧 Configurable**: Customizable settings via config.ini
- **🌐 Dual Connectivity**: Supports both ADB over USB and ADB over WiFi
- **🚀 Complete Installation**: Automated dependency detection and installation

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** with pip
- **Android device** with USB debugging enabled
- **Windows 10/11** (currently supported)

**Note**: ADB (Android Debug Bridge) will be automatically downloaded and installed during setup if not found.

### Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/aaronvstory/rtmp-stream-setup.git
   cd rtmp-stream-setup
   ```

2. **Run the automated setup** (Recommended)
   ```bash
   setup.bat
   ```
   This comprehensive setup script will:
   - ✅ Install Python dependencies automatically
   - ✅ Download and install ADB if not found
   - ✅ Verify MonaServer installation
   - ✅ Configure optimal settings
   - ✅ Provide detailed guidance and troubleshooting

3. **Launch the application**
   ```bash
   launch_rtmp_setup.bat
   ```

## 📱 Device Connection Methods

### USB Connection (Recommended for First Setup)

1. **Enable Developer Options**:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Return to Settings → Developer Options

2. **Enable USB Debugging**:
   - Developer Options → USB Debugging (ON)
   - USB Debugging (Security Settings) (ON) - if available

3. **Connect Device**:
   - Connect via USB cable
   - Accept "USB Debugging" prompt on device
   - Select "Always allow from this computer"

### WiFi Connection (ADB over WiFi)

**Important**: WiFi connection requires initial USB setup for security.

#### Method 1: Using Application (Easiest)
1. Connect device via USB first
2. Run the RTMP Setup Assistant
3. Application will detect device and offer WiFi setup option

#### Method 2: Manual Setup
1. **Initial USB Connection**:
   ```bash
   # Connect device via USB and enable WiFi mode
   adb tcpip 5555
   ```

2. **Find Device IP Address**:
   ```bash
   # Get device IP address
   adb shell ip route | grep wlan0
   # Or check in device Settings → WiFi → Advanced → IP Address
   ```

3. **Connect via WiFi**:
   ```bash
   # Replace DEVICE_IP with actual IP address
   adb connect DEVICE_IP:5555
   ```

4. **Disconnect USB**: You can now unplug the USB cable

5. **Verify Connection**:
   ```bash
   adb devices
   # Should show: DEVICE_IP:5555    device
   ```

#### WiFi Troubleshooting
- **Connection Lost**: Device IP may change; reconnect USB and repeat setup
- **Firewall Issues**: Ensure Windows Firewall allows ADB (port 5555)
- **Network Issues**: Device and computer must be on same WiFi network
- **Reset to USB**: Run `adb usb` and reconnect USB cable

## 🎮 Usage Guide

### First Run Configuration

On first launch, the application will guide you through configuring:

1. **ADB Path**: Auto-detected or manually selected during setup
2. **MonaServer Path**: Built-in RTMP server (bundled with project)
3. **OBS Path**: Optional OBS Studio executable path

### Streaming Workflow

1. **Connect Device**: USB or WiFi (see connection methods above)
2. **Launch Application**: Run `launch_rtmp_setup.bat`
3. **Follow Prompts**: The app will automatically:
   - Detect your device (shows connection type: USB 🔌, WiFi 📶, or Emulator 💻)
   - Set up port forwarding (device:1935 ↔ host:1935)
   - Start MonaServer
   - Launch your streaming app
   - Copy RTMP URL to clipboard

### RTMP Streaming URLs

#### Default URL
```
rtmp://127.0.0.1:1935/live
```

#### Custom Stream Names
For custom stream identifiers, append to the URL:
```
rtmp://127.0.0.1:1935/live/YOUR_CUSTOM_NAME
```

**Examples**:
- `rtmp://127.0.0.1:1935/live/mystream`
- `rtmp://127.0.0.1:1935/live/gaming_session`
- `rtmp://127.0.0.1:1935/live/presentation_2024`

#### Using Custom URLs
1. **In Streaming Apps**: Enter the custom URL in RTMP settings
2. **For Recording**: Use custom names to organize different streams
3. **Multiple Streams**: Each custom name creates a separate stream endpoint

## ⚙️ Configuration

### config.ini Settings

```ini
[Paths]
adbpath = C:\platform-tools\adb.exe
monaserverpath = .\MonaServer_Win64\MonaServer.exe
obspath = C:\Program Files\obs-studio\bin\64bit\obs64.exe

[Device]
packagename = com.telegram.a1064/com.nvshen.chmp4.SplashActivity

[Network]
rtmpport = 1935

[Options]
autostartmonaserver = true
autoselectsingledevice = true
fetchdevicemodels = true
forcekillconflictingportprocess = true
```

### Customization Options

- **Package Name**: Change the default app launched on device
- **RTMP Port**: Modify the streaming port (default: 1935)
- **Auto-start MonaServer**: Toggle automatic server startup
- **Device Model Fetching**: Enable/disable device model detection
- **Port Conflict Resolution**: Automatically kill conflicting processes

### Supported Streaming Apps

- **Telegram** (default configuration)
- **Any RTMP-capable mobile streaming app**
- **Custom apps**: Configure package name in config.ini

To find package names for other apps:
```bash
# List installed packages on device
adb shell pm list packages | grep -i "app_name"

# Get package name of currently running app
adb shell dumpsys window windows | grep -E 'mCurrentFocus'
```

## 🔧 Troubleshooting

### Common Issues

**ADB Not Found**
- Run `setup.bat` for automatic installation
- Manually download from [Android Developer site](https://developer.android.com/studio/releases/platform-tools)
- Ensure ADB is in system PATH or configure path in application

**Device Not Detected**
- Enable Developer Options and USB Debugging
- Try different USB cable/port
- Accept USB debugging prompt on device
- For WiFi: Ensure same network and correct IP address

**Port 1935 in Use**
- Application automatically detects and resolves conflicts
- Manually kill processes using port 1935: `netstat -ano | findstr :1935`
- Run application as Administrator for enhanced permissions

**MonaServer Fails to Start**
- Check Windows Firewall settings for port 1935
- Ensure MonaServer.exe is not blocked by antivirus
- Run application as Administrator
- Verify MonaServer_Win64 directory is complete

**WiFi Connection Issues**
- Reset to USB: `adb usb` then reconnect USB cable
- Restart ADB server: `adb kill-server` then `adb start-server`
- Check device IP hasn't changed: Settings → WiFi → Advanced
- Ensure both device and computer on same WiFi network

**Streaming App Won't Launch**
- Verify package name in config.ini is correct
- Install target app on device
- Grant necessary permissions to app
- Check app is compatible with RTMP streaming

### Debug Mode

For verbose logging:
1. Check MonaServer.log directory for server logs
2. Enable debug output in config.ini
3. Run application from command prompt to see detailed output

## 📁 Project Structure

```
rtmp-stream-setup/
├── launch_rtmp_setup.bat    # Main launcher script
├── setup.bat               # Comprehensive setup with auto-install
├── setupRTMP6.py           # Main Python application
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── MonaServer_Win64/       # RTMP server directory
│   ├── MonaServer.exe      # RTMP server executable
│   ├── MonaServer.ini      # Server configuration
│   ├── cert.pem           # SSL certificate
│   ├── key.pem            # SSL private key
│   ├── lua51.dll          # Lua runtime
│   └── www/               # Web server files
├── README.md              # This file
├── CHANGELOG.md           # Version history
├── LICENSE               # MIT License
└── .gitignore           # Git exclusions
```

## 🛠️ Dependencies

### Python Packages
- **rich**: Beautiful terminal output and UI components
- **pyperclip**: Clipboard management for RTMP URLs  
- **psutil**: System process and port management
- **tkinter**: File/folder selection dialogs (built-in)

### System Requirements
- **Python 3.7+**: Core runtime
- **ADB (Android Debug Bridge)**: Device communication (auto-installed)
- **MonaServer**: RTMP streaming server (bundled)

## 🎯 Advanced Usage

### Multiple Device Setup
The application supports multiple connected devices and will present a selection menu:
- USB devices show as 🔌
- WiFi devices show as 📶  
- Emulators show as 💻

### Custom Port Configuration
To use a different RTMP port:
1. Edit `config.ini` → `[Network]` → `rtmpport = YOUR_PORT`
2. Update streaming app settings to match
3. Ensure firewall allows the new port

### OBS Studio Integration
If OBS Studio is installed, the application can automatically open it:
1. Configure OBS path in setup or config.ini
2. Set up RTMP source with URL: `rtmp://127.0.0.1:1935/live`
3. Application will launch OBS after setting up the stream

### Batch Streaming
For automated streaming setups:
1. Configure all paths in config.ini
2. Use command line: `python setupRTMP6.py`
3. Application can be scripted for CI/CD workflows

## 🔒 Security Features

- **Port Conflict Detection**: Automatically handles port conflicts safely
- **Process Management**: Safe process termination and verification
- **Input Validation**: Secure path and configuration handling
- **No Credential Storage**: No sensitive data stored in configuration files
- **SSL Support**: MonaServer includes SSL certificates for secure streaming

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup
1. Clone repository
2. Run `setup.bat` for dependencies
3. Make your changes
4. Test with both USB and WiFi connections
5. Submit pull request

## 🆘 Support

If you encounter any issues:

1. **Check Troubleshooting**: Review the troubleshooting section above
2. **Run Setup Again**: Try `setup.bat` to reconfigure components
3. **Check Logs**: Review MonaServer logs in `MonaServer_Win64/MonaServer.log/`
4. **GitHub Issues**: Open an issue with detailed error information and system specs

## 🏷️ Version History

- **v3.0.0**: Enhanced setup with auto-installation, WiFi support, comprehensive documentation
- **v2.0.0**: Added Rich UI and improved device detection
- **v1.0.0**: Initial release with basic RTMP setup functionality

---

**Made with ❤️ for the streaming community**

**Supports both USB and WiFi connections for maximum flexibility!** 📱🔌📶