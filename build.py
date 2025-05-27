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
    """Create distribution package"""
    print("Creating distribution package...")
    
    system = platform.system().lower()
    dist_path = Path("dist")
    
    if system == "windows":
        # Create ZIP package
        package_name = "mitotic-spindle-tool-windows.zip"
        package_path = dist_path / package_name
        
        import zipfile
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(executable_path, executable_path.name)
            zipf.write(launcher_path, launcher_path.name)
        
    else:
        # Create tar.gz package
        package_name = f"mitotic-spindle-tool-{system}.tar.gz"
        package_path = dist_path / package_name
        
        import tarfile
        with tarfile.open(package_path, 'w:gz') as tarf:
            tarf.add(executable_path, executable_path.name)
            tarf.add(launcher_path, launcher_path.name)
    
    print(f"[SUCCESS] Created package: {package_path}")
    return package_path

def create_appimage():
    """Create AppImage for Linux (if tools are available)"""
    if platform.system().lower() != "linux":
        return None
    
    if not shutil.which("appimagetool"):
        print("[WARNING] appimagetool not found, skipping AppImage creation")
        return None
    
    print("Creating AppImage...")
    
    # Create AppDir structure
    appdir = Path("dist/AppDir")
    appdir.mkdir(exist_ok=True)
    
    (appdir / "usr/bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/applications").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy("dist/mitotic-spindle-tool", appdir / "usr/bin/")
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Type=Application
Name=Mitotic Spindle Tool
Comment=Image analysis tool for mitotic spindle analysis
Exec=mitotic-spindle-tool
Icon=mitotic-spindle-tool
Categories=Science;Education;
Terminal=false
"""
    
    with open(appdir / "usr/share/applications/mitotic-spindle-tool.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Create AppRun
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/mitotic-spindle-tool" "$@"
"""
    
    apprun_path = appdir / "AppRun"
    with open(apprun_path, 'w') as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)
    
    # Create AppImage
    try:
        os.chdir("dist")
        run_command(["appimagetool", "AppDir", "mitotic-spindle-tool.AppImage"])
        os.chdir("..")
        
        appimage_path = Path("dist/mitotic-spindle-tool.AppImage")
        if appimage_path.exists():
            os.chmod(appimage_path, 0o755)
            print(f"[SUCCESS] Created AppImage: {appimage_path}")
            return appimage_path
    except Exception as e:
        print(f"[WARNING] AppImage creation failed: {e}")
        os.chdir("..")
    
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
        
        # Try to create AppImage on Linux
        appimage_path = create_appimage()
        
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
