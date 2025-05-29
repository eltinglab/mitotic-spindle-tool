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

# Get the root directory of the project (parent of .github)
script_dir = Path(__file__).parent
root_dir = script_dir.parent.parent.parent  # Go up from build-scripts -> workflows -> .github -> root
os.chdir(root_dir)  # Change to root directory for the build process

# Add src to path to import version
sys.path.insert(0, os.path.join(root_dir, 'src'))
from version import __version__, VERSION_DISPLAY

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


def get_platform_executable_name():
    """Get platform-specific executable name"""
    system = platform.system().lower()
    if system == "windows":
        return "mitotic-spindle-tool-win.exe"
    elif system == "linux":
        return "mitotic-spindle-tool-linux"
    elif system == "darwin":
        return "mitotic-spindle-tool-macos"
    else:
        return "mitotic-spindle-tool"


def get_platform_package_name():
    """Get platform-specific package name"""
    system = platform.system().lower()
    if system == "windows":
        return "mitotic-spindle-tool-win.exe"  # Windows doesn't need additional packaging
    elif system == "linux":
        return "mitotic-spindle-tool-linux.tar.gz"
    elif system == "darwin":
        return "mitotic-spindle-tool-macos.dmg"
    else:
        return "mitotic-spindle-tool.tar.gz"


def get_platform_appimage_name():
    """Get platform-specific AppImage name"""
    return "mitotic-spindle-tool-linux.AppImage"

def build_with_pyinstaller(python_executable):
    """Build executable with PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Get the spec file path relative to root directory
    spec_file = ".github/workflows/build-scripts/mitotic-spindle-tool.spec"
    
    # Use system python if we couldn't set up venv properly
    if python_executable == sys.executable:
        cmd = [sys.executable, "-m", "PyInstaller", spec_file]
    else:
        cmd = [python_executable, "-m", "PyInstaller", spec_file]
    
    try:
        # Run PyInstaller
        result = run_command(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller failed with virtual env python: {e}")
        print("Trying with system python...")
        result = run_command([sys.executable, "-m", "PyInstaller", spec_file])
    
    system = platform.system().lower()
    if system == "windows":
        executable_name = "mitotic-spindle-tool.exe"
    else:
        executable_name = "mitotic-spindle-tool"
    
    executable_path = Path("dist") / executable_name
    
    # Rename executable with platform suffix for final distribution
    final_executable_name = get_platform_executable_name()
    final_executable_path = Path("dist") / final_executable_name
    
    if executable_path.exists() and final_executable_name != executable_name:
        shutil.copy2(executable_path, final_executable_path)
        print(f"[INFO] Created platform-specific executable: {final_executable_path}")
        # Keep original for compatibility with other build steps
    
    executable_path = final_executable_path if final_executable_path.exists() else executable_path
    
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
        # macOS - create proper app bundle and DMG
        package_name = get_platform_package_name()
        package_path = dist_path / package_name
        
        try:
            # Create proper macOS .app bundle
            app_bundle_path = create_macos_app_bundle(executable_path, dist_path)
            
            if app_bundle_path:
                # Create DMG with the app bundle
                dmg_temp_dir = dist_path / "dmg_temp"
                dmg_temp_dir.mkdir(exist_ok=True)
                
                # Copy app bundle to temp directory
                app_name = app_bundle_path.name
                dmg_app_path = dmg_temp_dir / app_name
                shutil.copytree(app_bundle_path, dmg_app_path)
                
                # Create Applications symlink for easy installation
                applications_link = dmg_temp_dir / "Applications"
                if not applications_link.exists():
                    os.symlink("/Applications", applications_link)
                
                # Create background image folder (optional)
                dmg_bg_dir = dmg_temp_dir / ".background"
                dmg_bg_dir.mkdir(exist_ok=True)
                
                # Copy icon for volume
                icon_source = Path("icons/EltingLabSpindle_512x512.png")
                if icon_source.exists():
                    shutil.copy2(icon_source, dmg_temp_dir / ".VolumeIcon.icns")
                
                # Create DMG
                run_command([
                    "hdiutil", "create", 
                    "-volname", "Mitotic Spindle Tool",
                    "-srcfolder", str(dmg_temp_dir),
                    "-ov", "-format", "UDZO",
                    str(package_path)
                ])
                
                # Clean up temp directory
                shutil.rmtree(dmg_temp_dir)
                
                print(f"[SUCCESS] Created DMG with app bundle: {package_path}")
                return package_path
            else:
                print("[WARNING] App bundle creation failed, falling back to basic DMG")
                raise subprocess.CalledProcessError(1, "app bundle creation")
            
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] DMG creation failed: {e}, falling back to tar.gz")
            # Fallback to tar.gz on macOS if DMG creation fails
            package_name = get_platform_package_name().replace('.dmg', '.tar.gz')
            package_path = dist_path / package_name
            
            import tarfile
            with tarfile.open(package_path, 'w:gz') as tarf:
                tarf.add(executable_path, executable_path.name)
                tarf.add(launcher_path, launcher_path.name)
            
            print(f"[SUCCESS] Created package: {package_path}")
            return package_path
        
    else:
        # Linux - create tar.gz with executable and launcher
        package_name = get_platform_package_name()
        package_path = dist_path / package_name
        
        import tarfile
        with tarfile.open(package_path, 'w:gz') as tarf:
            tarf.add(executable_path, executable_path.name)
            tarf.add(launcher_path, launcher_path.name)
        
        print(f"[SUCCESS] Created package: {package_path}")
        return package_path

def create_macos_app_bundle(executable_path, dist_path):
    """Create a proper macOS .app bundle"""
    if platform.system().lower() != "darwin":
        return None
    
    app_name = "Mitotic Spindle Tool.app"
    app_bundle_path = dist_path / app_name
    
    print(f"Creating macOS app bundle: {app_bundle_path}")
    
    # Create app bundle directory structure
    contents_dir = app_bundle_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Create directories
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy executable to MacOS directory
        app_executable = macos_dir / "mitotic-spindle-tool"
        shutil.copy2(executable_path, app_executable)
        os.chmod(app_executable, 0o755)
        
        # Create Info.plist
        info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Mitotic Spindle Tool</string>
    <key>CFBundleExecutable</key>
    <string>mitotic-spindle-tool</string>
    <key>CFBundleIconFile</key>
    <string>EltingLabSpindle</string>
    <key>CFBundleIdentifier</key>
    <string>edu.ncsu.physics.mitotic-spindle-tool</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Mitotic Spindle Tool</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{__version__}</string>
    <key>CFBundleVersion</key>
    <string>{__version__}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>tiff</string>
                <string>tif</string>
            </array>
            <key>CFBundleTypeName</key>
            <string>TIFF Image</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
        </dict>
    </array>
</dict>
</plist>"""
        
        with open(contents_dir / "Info.plist", 'w') as f:
            f.write(info_plist_content)
        
        # Create proper ICNS file for macOS from PNG icons
        icon_dest = resources_dir / "EltingLabSpindle.icns"
        icns_created = False
        
        # Try to create ICNS using iconutil (macOS built-in tool)
        if shutil.which("iconutil"):
            iconset_dir = resources_dir / "EltingLabSpindle.iconset"
            iconset_dir.mkdir(exist_ok=True)
            
            # Copy PNG files to iconset with proper naming
            icon_mappings = {
                "16x16": ["icon_16x16.png"],
                "32x32": ["icon_16x16@2x.png", "icon_32x32.png"],
                "64x64": ["icon_32x32@2x.png"],
                "128x128": ["icon_64x64@2x.png", "icon_128x128.png"],
                "256x256": ["icon_128x128@2x.png", "icon_256x256.png"],
                "512x512": ["icon_256x256@2x.png", "icon_512x512.png"],
            }
            
            iconset_files_created = 0
            for size, iconset_names in icon_mappings.items():
                png_source = Path(f"icons/EltingLabSpindle_{size}.png")
                if png_source.exists():
                    for iconset_name in iconset_names:
                        iconset_dest = iconset_dir / iconset_name
                        shutil.copy2(png_source, iconset_dest)
                        iconset_files_created += 1
            
            if iconset_files_created > 0:
                # Generate ICNS file
                try:
                    result = run_command([
                        "iconutil", "-c", "icns", 
                        str(iconset_dir), 
                        "-o", str(icon_dest)
                    ], check=False)
                    if result.returncode == 0 and icon_dest.exists():
                        icns_created = True
                        print(f"[SUCCESS] Created ICNS file using iconutil: {icon_dest}")
                    # Clean up iconset directory
                    shutil.rmtree(iconset_dir)
                except subprocess.CalledProcessError:
                    shutil.rmtree(iconset_dir)
        
        # Fallback: try using ImageMagick to convert PNG to ICNS
        if not icns_created and (shutil.which("magick") or shutil.which("convert")):
            png_files = []
            for size in [16, 32, 64, 128, 256, 512]:
                png_file = Path(f"icons/EltingLabSpindle_{size}x{size}.png")
                if png_file.exists():
                    png_files.append(str(png_file))
            
            if png_files:
                try:
                    magick_cmd = "magick" if shutil.which("magick") else "convert"
                    result = run_command([magick_cmd] + png_files + [str(icon_dest)], check=False)
                    if result.returncode == 0 and icon_dest.exists():
                        icns_created = True
                        print(f"[SUCCESS] Created ICNS file using {magick_cmd}: {icon_dest}")
                except subprocess.CalledProcessError:
                    pass
        
        # Final fallback: copy the largest PNG as icns (not ideal but works)
        if not icns_created:
            for size in [512, 256, 128, 64, 32, 16]:
                png_icon = Path(f"icons/EltingLabSpindle_{size}x{size}.png")
                if png_icon.exists():
                    shutil.copy2(png_icon, icon_dest)
                    print(f"[WARNING] Copied PNG as ICNS (fallback): {png_icon.name}")
                    break
        
        print(f"[SUCCESS] Created macOS app bundle: {app_bundle_path}")
        return app_bundle_path
        
    except Exception as e:
        print(f"[ERROR] Failed to create app bundle: {e}")
        if app_bundle_path.exists():
            shutil.rmtree(app_bundle_path)
        return None

def create_appimage():
    """Create AppImage for Linux (if tools are available)"""
    if platform.system().lower() != "linux":
        return None
    
    if not shutil.which("appimagetool"):
        print("[WARNING] appimagetool not found, skipping AppImage creation")
        return None
    
    print("Creating AppImage...")
    
    # Set environment variables for CI compatibility
    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        # Disable FUSE in CI environments where it might not be available
        env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    
    # Create AppDir structure
    appdir = Path("dist/AppDir")
    appdir.mkdir(exist_ok=True)
    
    (appdir / "usr/bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/applications").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/512x512/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/128x128/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/64x64/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/48x48/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/32x32/apps").mkdir(parents=True, exist_ok=True)
    (appdir / "usr/share/icons/hicolor/16x16/apps").mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy("dist/mitotic-spindle-tool", appdir / "usr/bin/")
    # Ensure executable has proper permissions
    os.chmod(appdir / "usr/bin/mitotic-spindle-tool", 0o755)
    
    # Copy icons at various sizes for proper desktop integration
    icons_dir = Path("icons")
    icon_sizes = {
        "512x512": "EltingLabSpindle_512x512.png",
        "256x256": "EltingLabSpindle_256x256.png", 
        "128x128": "EltingLabSpindle_128x128.png",
        "64x64": "EltingLabSpindle_64x64.png",
        "48x48": "EltingLabSpindle_48x48.png",
        "32x32": "EltingLabSpindle_32x32.png",
        "16x16": "EltingLabSpindle_16x16.png"
    }
    
    icons_copied = False
    for size, filename in icon_sizes.items():
        icon_path = icons_dir / filename
        if icon_path.exists():
            dest_path = appdir / f"usr/share/icons/hicolor/{size}/apps/mitotic-spindle-tool.png"
            shutil.copy(icon_path, dest_path)
            print(f"[SUCCESS] Copied icon {filename} to AppImage")
            icons_copied = True
    
    # Copy main icon to AppDir root for AppImage integration
    main_icon_candidates = [
        icons_dir / "EltingLabSpindle_256x256.png",
        icons_dir / "EltingLabSpindle_128x128.png", 
        icons_dir / "EltingLabSpindle_512x512.png"
    ]
    
    for icon_path in main_icon_candidates:
        if icon_path.exists():
            shutil.copy(icon_path, appdir / "mitotic-spindle-tool.png")
            print(f"[SUCCESS] Copied main icon {icon_path.name} to AppImage root")
            break
    
    if not icons_copied:
        print("[WARNING] No icons were copied to AppImage - application may not show proper icon in desktop environments")
    
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
    
    # Write desktop file to the standard location
    with open(appdir / "usr/share/applications/mitotic-spindle-tool.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Also write desktop file to AppDir root (required by AppImage)
    with open(appdir / "mitotic-spindle-tool.desktop", 'w') as f:
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
    current_dir = os.getcwd()
    try:
        os.chdir("dist")
        
        # Make sure executable is executable
        executable_path = "AppDir/usr/bin/mitotic-spindle-tool"
        if os.path.exists(executable_path):
            os.chmod(executable_path, 0o755)
        
        # Run appimagetool with more verbose output and error handling
        print("Running appimagetool...")
        appimage_name = get_platform_appimage_name()
        result = subprocess.run(
            ["appimagetool", "--verbose", "AppDir", appimage_name], 
            env=env, 
            check=False, 
            capture_output=True, 
            text=True
        )
        
        # Print output for debugging
        if result.stdout:
            print(f"[INFO] appimagetool stdout: {result.stdout}")
        if result.stderr:
            print(f"[ERROR] appimagetool stderr: {result.stderr}")
        
        print(f"[INFO] appimagetool exit code: {result.returncode}")
        
        os.chdir(current_dir)
        
        appimage_path = Path("dist") / appimage_name
        if result.returncode == 0 and appimage_path.exists():
            os.chmod(appimage_path, 0o755)
            print(f"[SUCCESS] Created AppImage: {appimage_path}")
            return appimage_path
        else:
            print(f"[WARNING] AppImage creation failed - appimagetool exit code: {result.returncode}")
            return None
            
    except Exception as e:
        os.chdir(current_dir)
        print(f"[WARNING] AppImage creation failed with exception: {e}")
        return None

def prepare_icons():
    """Prepare and verify icons for the build process"""
    print("Preparing icons for build...")
    
    icons_dir = Path("icons")
    if not icons_dir.exists():
        print("[WARNING] Icons directory not found, creating...")
        icons_dir.mkdir(exist_ok=True)
        return False
    
    # Icon files we need for different platforms
    required_icons = {
        "ico": "EltingLabSpindle.ico",  # High-res multi-size .ico for Windows
        "png_512": "EltingLabSpindle_512x512.png",  # High-res for macOS DMG and Linux
        "png_256": "EltingLabSpindle_256x256.png",  # Medium res for Linux AppImage
        "png_128": "EltingLabSpindle_128x128.png",  # For various desktop integrations
        "png_64": "EltingLabSpindle_64x64.png",
        "png_48": "EltingLabSpindle_48x48.png",
        "png_32": "EltingLabSpindle_32x32.png",
        "png_16": "EltingLabSpindle_16x16.png"
    }
    
    icons_available = {}
    for icon_type, filename in required_icons.items():
        icon_path = icons_dir / filename
        if icon_path.exists():
            icons_available[icon_type] = icon_path
            print(f"[SUCCESS] Found {icon_type} icon: {filename}")
    
    # Ensure we have the essential icons
    if "ico" in icons_available:
        print(f"[SUCCESS] High-resolution Windows icon ready: {icons_available['ico'].name}")
    if "png_512" in icons_available:
        print(f"[SUCCESS] High-resolution macOS/Linux icon ready: {icons_available['png_512'].name}")
    
    return icons_available

def main():
    """Main build function"""
    print("=" * 60)
    print(f"Building Mitotic Spindle Tool {VERSION_DISPLAY}")
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
