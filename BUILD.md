# Building Mitotic Spindle Tool

This document explains how to build the Mitotic Spindle Tool into executable packages for different platforms.

## Quick Start

The easiest way to build for your current platform:

```bash
python build.py
```

This will create executables and packages in the `dist/` folder.

## Platform-Specific Instructions

### Linux

#### Method 1: Using the build script
```bash
chmod +x build-linux.sh
./build-linux.sh
```

#### Method 2: Using Python build script
```bash
python build.py
```

#### Output Files:
- `dist/mitotic-spindle-tool` - Standalone executable
- `dist/run-mitotic-spindle-tool.sh` - Launcher script
- `dist/mitotic-spindle-tool-linux.tar.gz` - Distribution package
- `dist/mitotic-spindle-tool.AppImage` - AppImage (if appimagetool is available)

### Windows

#### Method 1: Using the batch script
```cmd
build-windows.bat
```

#### Method 2: Using Python build script
```cmd
python build.py
```

#### Output Files:
- `dist/mitotic-spindle-tool.exe` - Standalone executable
- `dist/run-mitotic-spindle-tool.bat` - Launcher script
- `dist/mitotic-spindle-tool-windows.zip` - Distribution package

### macOS

```bash
python build.py
```

#### Output Files:
- `dist/mitotic-spindle-tool` - Standalone executable
- `dist/run-mitotic-spindle-tool.sh` - Launcher script
- `dist/mitotic-spindle-tool-darwin.tar.gz` - Distribution package
- `dist/Mitotic Spindle Tool.app` - macOS app bundle (if configured)

## Requirements

### Build Dependencies
- Python 3.8 or higher
- pip (Python package manager)

### Automatic Installation
The build scripts will automatically install:
- PyInstaller (for creating executables)
- All project dependencies from `requirements.txt`

### Optional Dependencies
- **Linux**: `appimagetool` for creating AppImage files
- **Windows**: PowerShell for creating ZIP packages
- **macOS**: Xcode command line tools

## Manual Build Process

If you prefer to build manually:

### 1. Create Virtual Environment
```bash
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 3. Build Executable
```bash
pyinstaller mitotic-spindle-tool.spec
```

### 4. Test the Executable
```bash
# Linux/macOS
./dist/mitotic-spindle-tool

# Windows
dist\mitotic-spindle-tool.exe
```

## Customization

### Modifying the Build

#### Adding an Icon
1. Place your icon file in the project root (e.g., `icon.ico` for Windows, `icon.png` for Linux)
2. Edit `mitotic-spindle-tool.spec` and update the `icon` parameter:
   ```python
   exe = EXE(
       # ... other parameters ...
       icon='icon.ico',  # Add this line
   )
   ```

#### Changing the Executable Name
Edit `mitotic-spindle-tool.spec` and change the `name` parameter:
```python
exe = EXE(
    # ... other parameters ...
    name='your-custom-name',
)
```

#### Adding Data Files
If your application needs additional data files, add them to the `datas` list in `mitotic-spindle-tool.spec`:
```python
a = Analysis(
    # ... other parameters ...
    datas=[
        ('data/config.json', 'data'),
        ('resources/*', 'resources'),
    ],
)
```

### Build Configuration

#### Debug Build
To create a debug build with console output, edit `mitotic-spindle-tool.spec`:
```python
exe = EXE(
    # ... other parameters ...
    console=True,  # Change to True
    debug=True,    # Add this line
)
```

#### Optimizing File Size
- Use UPX compression (enabled by default)
- Exclude unnecessary modules in the `excludes` list
- Use one-file mode (default) vs one-directory mode

## Troubleshooting

### Common Issues

#### "Python not found"
- Ensure Python 3.8+ is installed and in your PATH
- Try using `python3` instead of `python`

#### "Module not found" errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using the correct virtual environment

#### Large executable size
- PyInstaller bundles all dependencies, resulting in larger files
- This is normal and ensures the executable runs on systems without Python

#### Permission errors (Linux/macOS)
```bash
chmod +x build-linux.sh
chmod +x dist/mitotic-spindle-tool
```

#### Missing DLLs (Windows)
- Install Microsoft Visual C++ Redistributable
- The build script includes most required libraries

### Getting Help

If you encounter issues:
1. Check the build output for specific error messages
2. Ensure all requirements are met
3. Try building in a fresh virtual environment
4. Consult the PyInstaller documentation for advanced issues

## Distribution

### Recommended Distribution Methods

#### Linux
- **AppImage**: Single file that runs on most Linux distributions
- **Tarball**: Extract and run, includes launcher script
- **Flatpak/Snap**: Consider these for wider distribution (requires additional setup)

#### Windows
- **Standalone EXE**: Single file executable
- **ZIP package**: Includes launcher script for convenience
- **Installer**: Consider using NSIS or similar for professional distribution

#### macOS
- **App Bundle**: Standard macOS application format
- **DMG**: Disk image for easy distribution
- **Homebrew**: For developer-friendly distribution

## Advanced Topics

### Cross-Platform Building
While the build scripts are designed for the current platform, you can potentially cross-compile using:
- Docker containers with different OS environments
- GitHub Actions for automated multi-platform builds
- Virtual machines for testing on different platforms

### Continuous Integration
The project includes configuration for automated building using GitHub Actions or similar CI/CD platforms.

### Code Signing
For production distribution, consider code signing:
- **Windows**: Use Microsoft Authenticode
- **macOS**: Use Apple Developer certificates
- **Linux**: Use GPG signatures for packages
