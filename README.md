# RTMP Stream Setup Assistant

A comprehensive tool for setting up RTMP streaming from Android devices with a beautiful terminal interface. This application automatically configures port forwarding, manages MonaServer, and provides a seamless streaming experience.

## ✨ Features

- **🎯 Automatic Setup**: One-click RTMP streaming configuration
- **📱 Device Detection**: Auto-detects connected Android devices
- **🔄 Port Management**: Handles port conflicts and forwarding automatically  
- **🎨 Rich UI**: Beautiful terminal interface with progress bars and status updates
- **⚙️ MonaServer Integration**: Built-in RTMP server with optimized configuration
- **📋 Clipboard Support**: Automatically copies RTMP URLs to clipboard
- **🔧 Configurable**: Customizable settings via config.ini

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** with pip
- **Android Debug Bridge (ADB)** 
- **Android device** with USB debugging enabled
- **Windows 10/11** (currently supported)

### Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/yourusername/rtmp-stream-setup.git
   cd rtmp-stream-setup
   ```

2. **Run the setup script**
   ```bash
   setup.bat
   ```
   This will automatically install all Python dependencies.

3. **Launch the application**
   ```bash
   launch_rtmp_setup.bat
   ```

## 🎮 Usage Guide

### First Run Configuration

On first launch, the application will guide you through configuring:

1. **ADB Path**: Location of your Android Debug Bridge executable
2. **MonaServer Path**: Built-in RTMP server (auto-detected)
3. **OBS Path**: Optional OBS Studio executable path

### Streaming Workflow

1. **Connect Device**: USB connect your Android device
2. **Enable Debugging**: Ensure USB debugging is enabled
3. **Launch Application**: Run `launch_rtmp_setup.bat`
4. **Follow Prompts**: The app will automatically:
   - Detect your device
   - Set up port forwarding (device:1935 ↔ host:1935)
   - Start MonaServer
   - Launch your streaming app
   - Copy RTMP URL to clipboard

### RTMP URL Format
```
rtmp://127.0.0.1:1935/live
```

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

## 🔧 Troubleshooting

### Common Issues

**Python not found**
- Install Python 3.7+ from [python.org](https://python.org)
- Ensure "Add Python to PATH" is checked during installation

**ADB not found**
- Download Android Platform Tools
- Extract to `C:\platform-tools\`
- Or use the path selection during first run

**Device not detected**
- Enable Developer Options on Android
- Turn on USB Debugging
- Accept USB debugging prompt on device
- Try different USB cable/port

**Port 1935 in use**
- Application will automatically detect and resolve conflicts
- Or manually kill processes using port 1935

**MonaServer fails to start**
- Check Windows Firewall settings
- Ensure port 1935 is available
- Run application as Administrator

### Debug Mode

For verbose logging, check the MonaServer.log directory for detailed server logs.

## 📁 Project Structure

```
rtmp-stream-setup/
├── launch_rtmp_setup.bat    # Main launcher script
├── setup.bat               # First-time setup script
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
└── LICENSE               # License information
```

## 🛠️ Dependencies

- **rich**: Beautiful terminal output and UI components
- **pyperclip**: Clipboard management for RTMP URLs  
- **psutil**: System process and port management
- **tkinter**: File/folder selection dialogs (built-in)

## 🎯 Supported Streaming Apps

- **Telegram** (default)
- **Any RTMP-capable mobile app**
- Custom package names can be configured

## 🔒 Security Features

- **Port Conflict Detection**: Automatically handles port conflicts
- **Process Management**: Safe process termination
- **Input Validation**: Secure path and configuration handling
- **No Credential Storage**: No sensitive data stored in files

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review MonaServer logs in `MonaServer_Win64/MonaServer.log/`
3. Open an issue on GitHub with detailed error information

## 🏷️ Version History

- **v3.0**: Enhanced port conflict detection and resolution
- **v2.0**: Added Rich UI and improved device detection
- **v1.0**: Initial release with basic RTMP setup functionality

---

**Made with ❤️ for the streaming community**