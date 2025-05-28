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
        # macOS - create branded DMG file
        package_name = "mitotic-spindle-tool-macos.dmg"
        package_path = dist_path / package_name
        
        try:
            # Try using enhanced DMG creation script first
            create_dmg_script = Path("create_dmg.py")
            if create_dmg_script.exists():
                print("Using enhanced DMG creation...")
                result = run_command([
                    sys.executable, str(create_dmg_script), 
                    str(executable_path), str(package_path)
                ], check=False)
                
                if result.returncode == 0 and package_path.exists():
                    print(f"[SUCCESS] Created branded DMG: {package_path}")
                    return package_path
                else:
                    print("[WARNING] Enhanced DMG creation failed, falling back to basic DMG")
            
            # Fallback to basic DMG creation
            dmg_temp_dir = dist_path / "dmg_temp"
            dmg_temp_dir.mkdir(exist_ok=True)
            
            # Copy executable and launcher to temp directory
            shutil.copy2(executable_path, dmg_temp_dir / executable_path.name)
            shutil.copy2(launcher_path, dmg_temp_dir / launcher_path.name)
            
            # Copy icon for DMG
            icon_source = Path("icons/EltingLabSpindle_512x512.png")
            if icon_source.exists():
                shutil.copy2(icon_source, dmg_temp_dir / "icon.png")
            
            # Create basic DMG
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

def prepare_icons():
    """Prepare and verify icons for the build process"""
    print("Preparing icons for build...")
    
    icons_dir = Path("icons")
    if not icons_dir.exists():
        print("[WARNING] Icons directory not found, creating...")
        icons_dir.mkdir(exist_ok=True)
        return False
    
    required_icons = {
        "ico": "EltingLabSpindle.ico",  # For Windows executable
        "png_512": "EltingLabSpindle_512x512.png",  # For DMG
        "png_256": "EltingLabSpindle_256x256.png",  # Backup for DMG
    }
    
    icons_available = {}
    for icon_type, filename in required_icons.items():
        icon_path = icons_dir / filename
        if icon_path.exists():
            icons_available[icon_type] = icon_path
            print(f"[SUCCESS] Found {icon_type} icon: {filename}")
        else:
            print(f"[WARNING] Missing {icon_type} icon: {filename}")
    
    return icons_available

def main():
    """Main build function"""
    print("=" * 60)
    print("Building Mitotic Spindle Tool")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print("=" * 60)
    
    try:
        # Prepare icons first
        icons_available = prepare_icons()
        
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
        
        # Show icon status
        if icons_available:
            print("\nIcons applied:")
            for icon_type, icon_path in icons_available.items():
                print(f"  - {icon_type}: {icon_path.name}")
        else:
            print("\n[WARNING] No icons were applied to the build")
        
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
