#!/usr/bin/env python3
"""
Cross-platform build script for Mitotic Spindle Tool
Supports Windows, Linux, and macOS
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    if isinstance(cmd, str):
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result

def setup_virtual_environment():
    """Set up and activate virtual environment"""
    print("Setting up virtual environment...")
    
    # Check if we're in CI environment - skip venv and use system Python
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("CI environment detected, using system Python...")
        return "pip", sys.executable
    
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            run_command([sys.executable, "-m", "venv", "venv"])
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Virtual environment creation failed: {e}")
            print("Falling back to system Python...")
            return "pip", sys.executable
    
    # Determine activation script path
    system = platform.system().lower()
    if system == "windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"
    
    # Verify that the executables exist
    if not pip_executable.exists() or not python_executable.exists():
        print("[WARNING] Virtual environment executables not found, using system Python...")
        return "pip", sys.executable
    
    return str(pip_executable), str(python_executable)

def install_dependencies(pip_executable):
    """Install project dependencies"""
    print("Installing dependencies...")
    
    try:
        # Upgrade pip
        run_command([pip_executable, "install", "--upgrade", "pip"])
        
        # Install project dependencies
        run_command([pip_executable, "install", "-r", "requirements.txt"])
        
        # Install build tools
        run_command([pip_executable, "install", "pyinstaller", "setuptools", "wheel"])
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Dependency installation failed: {e}")
        # Try with system pip if the virtual env pip fails
        if pip_executable != "pip":
            print("Trying with system pip...")
            run_command(["pip", "install", "--upgrade", "pip"])
            run_command(["pip", "install", "-r", "requirements.txt"])
            run_command(["pip", "install", "pyinstaller", "setuptools", "wheel"])

def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("Cleaning previous builds...")
    
    paths_to_clean = [
        "build",
        "dist", 
        "__pycache__",
        "src/__pycache__",
        "*.egg-info"
    ]
    
    for path in paths_to_clean:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

def build_with_pyinstaller(python_executable):
    """Build executable with PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Use system python if we couldn't set up venv properly
    if python_executable == sys.executable:
        cmd = [sys.executable, "-m", "PyInstaller", "mitotic-spindle-tool.spec"]
    else:
        cmd = [python_executable, "-m", "PyInstaller", "mitotic-spindle-tool.spec"]
    
    try:
        # Run PyInstaller
        result = run_command(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller failed with virtual env python: {e}")
        print("Trying with system python...")
        result = run_command([sys.executable, "-m", "PyInstaller", "mitotic-spindle-tool.spec"])
    
    system = platform.system().lower()
    if system == "windows":
        executable_name = "mitotic-spindle-tool.exe"
    else:
        executable_name = "mitotic-spindle-tool"
    
    executable_path = Path("dist") / executable_name
    
    if executable_path.exists():
        print(f"[SUCCESS] PyInstaller build successful: {executable_path}")
        return executable_path
    else:
        print("[ERROR] PyInstaller build failed!")
        return None

def create_launcher_scripts(executable_path):
    """Create launcher scripts for the executable"""
    print("Creating launcher scripts...")
    
    dist_path = Path("dist")
    system = platform.system().lower()
    
    if system == "windows":
        # Create batch launcher
        launcher_content = f"""@echo off
cd /d "%~dp0"
{executable_path.name} %*
"""
        launcher_path = dist_path / "run-mitotic-spindle-tool.bat"
        
    else:
        # Create shell launcher
        launcher_content = f"""#!/bin/bash
# Launcher script for Mitotic Spindle Tool

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the application
./{executable_path.name} "$@"
"""
        launcher_path = dist_path / "run-mitotic-spindle-tool.sh"
    
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    # Make executable on Unix systems
    if system != "windows":
        os.chmod(launcher_path, 0o755)
        os.chmod(executable_path, 0o755)
    
    print(f"[SUCCESS] Created launcher: {launcher_path}")
    return launcher_path

def create_distribution_package(executable_path, launcher_path):
    """Create distribution package according to platform conventions"""
    print("Creating distribution package...")
    
    system = platform.system().lower()
    dist_path = Path("dist")
    
    if system == "windows":
        # Windows - no packaging needed, just provide the .exe
        print(f"[SUCCESS] Windows executable ready: {executable_path}")
        return executable_path
        
    elif system == "darwin":
        # macOS - create DMG file
        package_name = "mitotic-spindle-tool-macos.dmg"
        package_path = dist_path / package_name
        
        try:
            # Create a temporary directory for DMG contents
            dmg_temp_dir = dist_path / "dmg_temp"
            dmg_temp_dir.mkdir(exist_ok=True)
            
            # Copy executable and launcher to temp directory
            shutil.copy2(executable_path, dmg_temp_dir / executable_path.name)
            shutil.copy2(launcher_path, dmg_temp_dir / launcher_path.name)
            
            # Create DMG using hdiutil (macOS built-in tool)
            run_command([
                "hdiutil", "create", 
                "-volname", "Mitotic Spindle Tool",
                "-srcfolder", str(dmg_temp_dir),
                "-ov", "-format", "UDZO",
                str(package_path)
            ])
            
            # Clean up temp directory
            shutil.rmtree(dmg_temp_dir)
            
            print(f"[SUCCESS] Created DMG: {package_path}")
            return package_path
            
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] DMG creation failed: {e}, falling back to tar.gz")
            # Fallback to tar.gz on macOS if DMG creation fails
            package_name = "mitotic-spindle-tool-macos.tar.gz"
            package_path = dist_path / package_name
            
            import tarfile
            with tarfile.open(package_path, 'w:gz') as tarf:
                tarf.add(executable_path, executable_path.name)
                tarf.add(launcher_path, launcher_path.name)
            
            print(f"[SUCCESS] Created package: {package_path}")
            return package_path
        
    else:
        # Linux - create tar.gz with executable and launcher
        package_name = "mitotic-spindle-tool-linux.tar.gz"
        package_path = dist_path / package_name
        
        import tarfile
        with tarfile.open(package_path, 'w:gz') as tarf:
            tarf.add(executable_path, executable_path.name)
            tarf.add(launcher_path, launcher_path.name)
        
        print(f"[SUCCESS] Created package: {package_path}")
        
        # Also try to create AppImage
        appimage_path = create_appimage()
        
        # Return the primary package (tar.gz) - AppImage is created as an additional option
        return package_path

def download_appimage_tools():
    """Download AppImageTool if not available"""
    print("Checking for AppImage tools...")
    
    # Check if appimagetool is available
    if shutil.which("appimagetool"):
        print("[INFO] appimagetool found in PATH")
        return True
    
    # Try to download appimagetool
    print("[INFO] appimagetool not found, downloading...")
    
    import urllib.request
    
    try:
        # Download appimagetool for x86_64
        tool_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        tool_path = Path("dist/appimagetool")
        
        print(f"Downloading {tool_url}...")
        urllib.request.urlretrieve(tool_url, tool_path)
        os.chmod(tool_path, 0o755)
        
        print(f"[SUCCESS] Downloaded appimagetool to {tool_path}")
        return str(tool_path)
        
    except Exception as e:
        print(f"[WARNING] Failed to download appimagetool: {e}")
        return None

def create_default_icon():
    """Create a simple default icon for the application"""
    icon_path = Path("dist/AppDir/usr/share/icons/hicolor/256x256/apps/mitotic-spindle-tool.png")
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create a simple SVG icon and convert to PNG
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#2E86AB" rx="20"/>
  <circle cx="128" cy="128" r="80" fill="none" stroke="#F24236" stroke-width="8"/>
  <circle cx="128" cy="128" r="40" fill="none" stroke="#F24236" stroke-width="4"/>
  <circle cx="128" cy="128" r="20" fill="none" stroke="#F24236" stroke-width="2"/>
  <text x="128" y="220" text-anchor="middle" fill="white" font-family="Arial" font-size="20" font-weight="bold">Spindle</text>
</svg>'''
        
        svg_path = Path("dist/temp_icon.svg")
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        # Try to convert SVG to PNG using different tools
        conversion_successful = False
        
        # Try ImageMagick
        if shutil.which("convert"):
            try:
                run_command([
                    "convert", str(svg_path), 
                    "-resize", "256x256",
                    str(icon_path)
                ])
                conversion_successful = True
                print("[SUCCESS] Created icon using ImageMagick")
            except:
                pass
        
        # Try Inkscape
        if not conversion_successful and shutil.which("inkscape"):
            try:
                run_command([
                    "inkscape", str(svg_path),
                    "--export-png", str(icon_path),
                    "--export-width", "256",
                    "--export-height", "256"
                ])
                conversion_successful = True
                print("[SUCCESS] Created icon using Inkscape")
            except:
                pass
        
        # Try rsvg-convert
        if not conversion_successful and shutil.which("rsvg-convert"):
            try:
                run_command([
                    "rsvg-convert", "-w", "256", "-h", "256",
                    str(svg_path), "-o", str(icon_path)
                ])
                conversion_successful = True
                print("[SUCCESS] Created icon using rsvg-convert")
            except:
                pass
        
        # Clean up SVG file
        if svg_path.exists():
            svg_path.unlink()
        
        if not conversion_successful:
            print("[WARNING] Could not convert SVG to PNG, skipping icon creation")
            return None
        
        return icon_path
        
    except Exception as e:
        print(f"[WARNING] Icon creation failed: {e}")
        return None

def create_appimage():
    """Create AppImage for Linux (if tools are available)"""
    if platform.system().lower() != "linux":
        return None
    
    print("Creating AppImage...")
    
    # Check for or download AppImage tools
    appimagetool_path = download_appimage_tools()
    if not appimagetool_path:
        print("[WARNING] AppImage tools not available, skipping AppImage creation")
        return None
    
    # Determine appimagetool command
    if appimagetool_path == True:
        appimagetool_cmd = "appimagetool"
    else:
        appimagetool_cmd = str(appimagetool_path)
    
    # Create AppDir structure
    appdir = Path("dist/AppDir")
    if appdir.exists():
        shutil.rmtree(appdir)
    appdir.mkdir(exist_ok=True)
    
    (appdir / "usr/bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/applications").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True, exist_ok=True)
    
    # Check if executable exists
    executable_path = Path("dist/mitotic-spindle-tool")
    if not executable_path.exists():
        print("[ERROR] Executable not found for AppImage creation")
        return None
    
    # Copy executable
    shutil.copy2(executable_path, appdir / "usr/bin/")
    
    # Use existing resized icon or create default
    elting_icon_path = Path("icons/EltingLabSpindle_256x256.png")
    if elting_icon_path.exists():
        icon_path = appdir / "usr/share/icons/hicolor/256x256/apps/mitotic-spindle-tool.png"
        shutil.copy2(elting_icon_path, icon_path)
        print(f"[SUCCESS] Using EltingLab icon: {elting_icon_path}")
    else:
        # Fallback to creating default icon
        icon_path = create_default_icon()
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Type=Application
Name=Mitotic Spindle Tool
Comment=Image analysis tool for mitotic spindle analysis
Exec=mitotic-spindle-tool
Icon=mitotic-spindle-tool
Categories=Science;Education;Graphics;
Terminal=false
StartupNotify=true
MimeType=image/tiff;image/tif;
"""
    
    desktop_file_path = appdir / "usr/share/applications/mitotic-spindle-tool.desktop"
    with open(desktop_file_path, 'w') as f:
        f.write(desktop_content)
    
    # Copy desktop file to AppDir root for AppImage
    shutil.copy2(desktop_file_path, appdir / "mitotic-spindle-tool.desktop")
    
    # Copy icon to AppDir root if it exists
    if icon_path and icon_path.exists():
        shutil.copy2(icon_path, appdir / "mitotic-spindle-tool.png")
        print(f"[SUCCESS] Copied icon to AppDir root: {icon_path}")
    elif elting_icon_path.exists():
        # Direct copy from EltingLab icon if the previous method didn't work
        shutil.copy2(elting_icon_path, appdir / "mitotic-spindle-tool.png")
        print(f"[SUCCESS] Used EltingLab icon for AppDir root: {elting_icon_path}")
    
    # Create AppRun
    apprun_content = """#!/bin/bash
# AppRun script for Mitotic Spindle Tool

HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

# Change to a writable directory for temporary files
cd "${HOME}"

exec "${HERE}/usr/bin/mitotic-spindle-tool" "$@"
"""
    
    apprun_path = appdir / "AppRun"
    with open(apprun_path, 'w') as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)
    
    # Create AppImage
    try:
        original_dir = os.getcwd()
        
        # Use absolute path for appimagetool
        if appimagetool_cmd != "appimagetool":
            appimagetool_cmd = os.path.abspath(appimagetool_cmd)
        
        os.chdir("dist")
        
        # Set ARCH environment variable for AppImage
        env = os.environ.copy()
        env['ARCH'] = 'x86_64'
        
        print(f"Running: {appimagetool_cmd} AppDir mitotic-spindle-tool.AppImage")
        result = subprocess.run([
            appimagetool_cmd, 
            "AppDir", 
            "mitotic-spindle-tool.AppImage"
        ], env=env, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        os.chdir(original_dir)
        
        appimage_path = Path("dist/mitotic-spindle-tool.AppImage")
        if appimage_path.exists():
            os.chmod(appimage_path, 0o755)
            print(f"[SUCCESS] Created AppImage: {appimage_path}")
            
            # Get file size for reporting
            size_mb = appimage_path.stat().st_size / (1024 * 1024)
            print(f"[INFO] AppImage size: {size_mb:.2f} MB")
            
            return appimage_path
        else:
            print("[ERROR] AppImage creation completed but file not found")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] AppImage creation failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        os.chdir(original_dir)
        return None
    except Exception as e:
        print(f"[WARNING] AppImage creation failed with unexpected error: {e}")
        os.chdir(original_dir)
        return None

def main():
    """Main build function"""
    print("=" * 60)
    print("Building Mitotic Spindle Tool")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print("=" * 60)
    
    try:
        # Setup environment
        pip_executable, python_executable = setup_virtual_environment()
        install_dependencies(pip_executable)
        
        # Clean and build
        clean_build_artifacts()
        executable_path = build_with_pyinstaller(python_executable)
        
        if not executable_path:
            print("Build failed!")
            return 1
        
        # Create additional files
        launcher_path = create_launcher_scripts(executable_path)
        package_path = create_distribution_package(executable_path, launcher_path)
        
        # Check if AppImage was created (Linux only)
        appimage_path = None
        if platform.system().lower() == "linux":
            appimage_path = Path("dist/mitotic-spindle-tool.AppImage")
            if not appimage_path.exists():
                appimage_path = None
        
        # Summary
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        print("Outputs:")
        print(f"  - Executable: {executable_path}")
        print(f"  - Launcher: {launcher_path}")
        print(f"  - Package: {package_path}")
        
        if appimage_path:
            print(f"  - AppImage: {appimage_path}")
        
        print("\nTo run the application:")
        print(f"  {executable_path}")
        print("or")
        print(f"  {launcher_path}")
        
        if appimage_path:
            print("or")
            print(f"  {appimage_path}")
        
        return 0
        
    except Exception as e:
        print(f"Build failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
