#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform build script for Mitotic Spindle Tool
Supports Windows, Linux, and macOS
"""

import os
import sys
import platform
import subprocess
import shutil
import tarfile
from pathlib import Path

# Ensure UTF-8 encoding for Windows compatibility
if platform.system() == "Windows":
    # Set console encoding to UTF-8 if possible
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass  # Fall back to default encoding

# Get the root directory of the project (parent of .github)
script_dir = Path(__file__).parent.absolute()
root_dir = script_dir.parent.parent.parent.absolute()  # Go up from build-scripts -> workflows -> .github -> root

# Add src to path to import version - use absolute path
sys.path.insert(0, str(root_dir / 'src'))
from version import __version__, VERSION_DISPLAY

# Store key directories as absolute paths for consistent access
ICONS_DIR = root_dir / "icons"
SRC_DIR = root_dir / "src"
DIST_DIR = root_dir / "dist"
SPEC_FILE = root_dir / ".github" / "workflows" / "build-scripts" / "mitotic-spindle-tool.spec"

def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    # Ensure UTF-8 encoding for subprocess on Windows
    encoding = 'utf-8' if platform.system() == "Windows" else None
    if isinstance(cmd, str):
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, 
                              text=True, encoding=encoding, errors='replace')
    else:
        result = subprocess.run(cmd, check=check, capture_output=capture_output, 
                              text=True, encoding=encoding, errors='replace')
    
    if capture_output:
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
        # Ensure PYTHONPATH is set for CI builds too
        os.environ["PYTHONPATH"] = os.path.join(root_dir, "src")
        return "pip", sys.executable
    
    # For local builds, use consistent module handling without forcing CI mode
    print("Local build detected, setting up consistent environment...")
    os.environ["PYTHONPATH"] = os.path.join(root_dir, "src")
    
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
    
    # Verify paths exist using absolute paths
    if not SPEC_FILE.exists():
        print(f"[ERROR] Spec file not found: {SPEC_FILE}")
        return None
    
    main_script = SRC_DIR / "spindleGUI.py"
    if not main_script.exists():
        print(f"[ERROR] Main script not found: {main_script}")
        return None
    
    icon_file = ICONS_DIR / "EltingLabSpindle.ico"
    if not icon_file.exists():
        print(f"[ERROR] Icon file not found: {icon_file}")
        return None
        
    print(f"[INFO] Working directory: {root_dir}")
    print(f"[INFO] Spec file path: {SPEC_FILE}")
    print(f"[INFO] Main script path: {main_script}")
    print(f"[INFO] Icon path: {icon_file}")
    print(f"[INFO] Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Verify all required modules exist
    src_modules = ['metadataDialog.py', 'manualSpindleDialog.py', 'plotDialog.py', 
                   'plotSpindle.py', 'curveFitData.py', 'threshFunctions.py', 
                   'tiffFunctions.py', 'version.py', 'keypress_method.py', 
                   'spindlePreviewDialog.py']
    
    for module in src_modules:
        module_path = SRC_DIR / module
        if module_path.exists():
            print(f"[INFO] [OK] Found module: {module}")
        else:
            print(f"[WARNING] [X] Missing module: {module}")
    
    # Set up environment for PyInstaller to find modules properly
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SRC_DIR)
    env['PYINSTALLER_ROOT_DIR'] = str(root_dir)  # Help spec file find project root
    
    # Copy runtime hook to ensure it's available for PyInstaller
    try:
        runtime_hook_source = script_dir / "runtime_hook_src_modules.py"
        if runtime_hook_source.exists():
            print(f"[INFO] [OK] Runtime hook found at {runtime_hook_source}")
        else:
            print(f"[WARNING] Runtime hook not found at {runtime_hook_source}")
    except Exception as e:
        print(f"[WARNING] Error checking runtime hook: {e}")
    
    # Use system python if we couldn't set up venv properly
    if python_executable == sys.executable:
        cmd = [sys.executable, "-m", "PyInstaller", str(SPEC_FILE)]
    else:
        cmd = [python_executable, "-m", "PyInstaller", str(SPEC_FILE)]
    
    try:
        # Run PyInstaller with output capture and custom environment
        # Change to root directory for PyInstaller execution
        print(f"[INFO] Running PyInstaller from directory: {root_dir}")
        print(f"[INFO] Running PyInstaller with PYTHONPATH: {env['PYTHONPATH']}")
        # Ensure UTF-8 encoding for subprocess on Windows
        encoding = 'utf-8' if platform.system() == "Windows" else None
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env,
                              encoding=encoding, errors='replace', cwd=str(root_dir))
        if result.returncode != 0:
            print(f"[ERROR] PyInstaller failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd)
        else:
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller failed with virtual env python: {e}")
        print("Trying with system python...")
        try:
            cmd_fallback = [sys.executable, "-m", "PyInstaller", str(SPEC_FILE)]
            # Ensure UTF-8 encoding for subprocess on Windows
            encoding = 'utf-8' if platform.system() == "Windows" else None
            result = subprocess.run(cmd_fallback, check=False, capture_output=True, text=True, env=env,
                                  encoding=encoding, errors='replace', cwd=str(root_dir))
            if result.returncode != 0:
                print(f"[ERROR] PyInstaller failed with system python too, return code {result.returncode}")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                print(f"Build failed with error: Command '{cmd_fallback}' returned non-zero exit status {result.returncode}.")
                sys.exit(1)
            else:
                print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
        except subprocess.CalledProcessError as e2:
            print(f"Build failed with error: {e2}")
            sys.exit(1)
    
    system = platform.system().lower()
    if system == "windows":
        executable_name = "mitotic-spindle-tool.exe"
    else:
        executable_name = "mitotic-spindle-tool"
    
    executable_path = DIST_DIR / executable_name
    
    # Rename executable with platform suffix for final distribution
    final_executable_name = get_platform_executable_name()
    final_executable_path = DIST_DIR / final_executable_name
    
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
    
    system = platform.system().lower()
    
    if system == "windows":
        # Create batch launcher
        launcher_content = f"""@echo off
cd /d "%~dp0"
{executable_path.name} %*
"""
        launcher_path = DIST_DIR / "run-mitotic-spindle-tool.bat"
        
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
        launcher_path = DIST_DIR / "run-mitotic-spindle-tool.sh"
    
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
    
    if system == "windows":
        # Windows - no packaging needed, just provide the .exe
        print(f"[SUCCESS] Windows executable ready: {executable_path}")
        return executable_path
        
    elif system == "darwin":
        # macOS - create proper app bundle and DMG
        package_name = get_platform_package_name()
        package_path = DIST_DIR / package_name
        
        try:
            # Create proper macOS .app bundle (works on any platform)
            app_bundle_path = create_macos_app_bundle(executable_path, DIST_DIR)
            
            if app_bundle_path:
                # Check if we can create a DMG (requires hdiutil)
                can_create_dmg = shutil.which("hdiutil") is not None
                current_platform = platform.system().lower()
                
                if can_create_dmg:
                    print(f"[INFO] Creating DMG on {current_platform} using hdiutil...")
                    
                    # Create DMG with the app bundle
                    dmg_temp_dir = DIST_DIR / "dmg_temp"
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
                    icon_source = ICONS_DIR / "EltingLabSpindle_512x512.png"
                    if icon_source.exists():
                        shutil.copy2(icon_source, dmg_temp_dir / ".VolumeIcon.icns")
                    
                    # Create a README for macOS users about security warnings
                    readme_content = """# Mitotic Spindle Tool - macOS Installation

## Security Notice
This application is not signed with an Apple Developer certificate, so macOS may show security warnings.

## Installation Steps
1. Drag "Mitotic Spindle Tool.app" to the Applications folder
2. If macOS blocks the app, follow these steps:

### Method 1: Right-click to Open
1. Right-click (or Control+click) on "Mitotic Spindle Tool.app" in Applications
2. Select "Open" from the context menu
3. Click "Open" in the security dialog

### Method 2: System Preferences
1. Go to Apple menu > System Preferences > Security & Privacy
2. Click the "General" tab
3. Look for a message about "Mitotic Spindle Tool" being blocked
4. Click "Open Anyway"

### Method 3: Terminal (Advanced)
If the above methods don't work, open Terminal and run:
```
sudo xattr -rd com.apple.quarantine "/Applications/Mitotic Spindle Tool.app"
```

## Why These Steps Are Needed
This application was built without an Apple Developer certificate ($99/year).
The app is safe to use and open source - you can verify the code at:
https://github.com/eltinglab/mitotic-spindle-tool

## Support
If you encounter issues, please report them at:
https://github.com/eltinglab/mitotic-spindle-tool/issues
"""
                    
                    readme_file = dmg_temp_dir / "README - IMPORTANT.txt"
                    with open(readme_file, 'w') as f:
                        f.write(readme_content)
                    
                    # Create DMG with better compression and verification
                    dmg_create_cmd = [
                        "hdiutil", "create", 
                        "-volname", "Mitotic Spindle Tool",
                        "-srcfolder", str(dmg_temp_dir),
                        "-ov", "-format", "UDZO",
                        "-imagekey", "zlib-level=9",  # Maximum compression
                        str(package_path)
                    ]
                    
                    # Add filesystem type for better compatibility
                    if current_platform == "darwin":
                        dmg_create_cmd.extend(["-fs", "HFS+"])
                    
                    result = run_command(dmg_create_cmd, check=False)
                    
                    if result.returncode == 0 and package_path.exists():
                        # Verify DMG was created successfully
                        verify_result = run_command([
                            "hdiutil", "verify", str(package_path)
                        ], check=False)
                        
                        if verify_result.returncode == 0:
                            print(f"[SUCCESS] Created and verified DMG: {package_path}")
                            
                            # Add platform-specific warnings
                            if current_platform != "darwin":
                                print("[WARNING] DMG created on non-macOS system:")
                                print("  - App bundle may need code signing on macOS")
                                print("  - Users may need to allow the app in System Preferences > Security & Privacy")
                                print("  - Consider notarizing the app for better user experience")
                        else:
                            print(f"[WARNING] DMG verification failed: {verify_result.stderr}")
                            print("DMG was created but may have issues")
                    else:
                        print(f"[ERROR] DMG creation failed: {result.stderr}")
                        raise subprocess.CalledProcessError(result.returncode, dmg_create_cmd)
                    
                    # Clean up temp directory
                    shutil.rmtree(dmg_temp_dir)
                    
                    return package_path
                else:
                    print(f"[WARNING] hdiutil not available on {current_platform}, falling back to tar.gz")
                    raise subprocess.CalledProcessError(1, "hdiutil not available")
            else:
                print("[WARNING] App bundle creation failed, falling back to tar.gz")
                raise subprocess.CalledProcessError(1, "app bundle creation")
            
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] DMG creation failed: {e}, falling back to tar.gz")
            # Fallback to tar.gz on macOS if DMG creation fails
            package_name = get_platform_package_name().replace('.dmg', '.tar.gz')
            package_path = DIST_DIR / package_name
            
            # If we have an app bundle, include it in the tar.gz
            if 'app_bundle_path' in locals() and app_bundle_path and app_bundle_path.exists():
                with tarfile.open(package_path, 'w:gz') as tarf:
                    tarf.add(app_bundle_path, app_bundle_path.name)
                    if launcher_path.exists():
                        tarf.add(launcher_path, launcher_path.name)
                print(f"[SUCCESS] Created macOS package with app bundle: {package_path}")
            else:
                # Fall back to just the executable
                with tarfile.open(package_path, 'w:gz') as tarf:
                    tarf.add(executable_path, executable_path.name)
                    tarf.add(launcher_path, launcher_path.name)
                print(f"[SUCCESS] Created fallback package: {package_path}")
            
            return package_path
        
    else:
        # Linux - create tar.gz with executable and launcher
        package_name = get_platform_package_name()
        package_path = DIST_DIR / package_name
        
        with tarfile.open(package_path, 'w:gz') as tarf:
            tarf.add(executable_path, executable_path.name)
            tarf.add(launcher_path, launcher_path.name)
        
        print(f"[SUCCESS] Created package: {package_path}")
        return package_path

def create_macos_app_bundle(executable_path, dist_path):
    """Create a proper macOS .app bundle"""
    # Note: We can create app bundles on any platform, but they may need signing on macOS
    app_name = "Mitotic Spindle Tool.app"
    app_bundle_path = dist_path / app_name
    
    print(f"Creating macOS app bundle: {app_bundle_path}")
    current_platform = platform.system().lower()
    
    if current_platform != "darwin":
        print(f"[WARNING] Creating macOS app bundle on {current_platform} - bundle may require additional steps on macOS")
    
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
        
        # Create Info.plist with additional security and compatibility keys
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
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
    </dict>
    <key>NSHumanReadableCopyright</key>
    <string>© 2025 NCSU Elting Lab. All rights reserved.</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.education</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
        <string>MacOSX</string>
    </array>
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
                png_source = ICONS_DIR / f"EltingLabSpindle_{size}.png"
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
                png_file = ICONS_DIR / f"EltingLabSpindle_{size}x{size}.png"
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
                png_icon = ICONS_DIR / f"EltingLabSpindle_{size}x{size}.png"
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
    
    # Set environment variables for AppImage creation
    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    # Note: Removed APPIMAGE_EXTRACT_AND_RUN=1 to fix hotkey issues
    # This allows AppImages to use FUSE mounting which preserves Qt focus handling
    
    # Create AppDir structure using absolute paths
    appdir = DIST_DIR / "AppDir"
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
    
    # Copy executable using absolute paths
    source_executable = DIST_DIR / "mitotic-spindle-tool"
    target_executable = appdir / "usr/bin/mitotic-spindle-tool"
    shutil.copy(source_executable, target_executable)
    # Ensure executable has proper permissions
    os.chmod(target_executable, 0o755)
    
    # Copy icons at various sizes for proper desktop integration
    # Use absolute path to ensure icon directory is found regardless of working directory
    print(f"[INFO] Looking for icons in: {ICONS_DIR}")
    print(f"[INFO] Icons directory exists: {ICONS_DIR.exists()}")
    
    if ICONS_DIR.exists():
        print(f"[INFO] Contents of icons directory: {list(ICONS_DIR.iterdir())}")
    
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
        icon_path = ICONS_DIR / filename
        print(f"[INFO] Checking icon: {icon_path} (exists: {icon_path.exists()})")
        if icon_path.exists():
            try:
                dest_path = appdir / f"usr/share/icons/hicolor/{size}/apps/mitotic-spindle-tool.png"
                shutil.copy(icon_path, dest_path)
                print(f"[SUCCESS] Copied icon {filename} to AppImage at {dest_path}")
                icons_copied = True
            except Exception as e:
                print(f"[ERROR] Failed to copy icon {filename}: {e}")
    
    # Copy main icon to AppDir root for AppImage integration
    main_icon_candidates = [
        ICONS_DIR / "EltingLabSpindle_256x256.png",
        ICONS_DIR / "EltingLabSpindle_128x128.png", 
        ICONS_DIR / "EltingLabSpindle_512x512.png"
    ]
    
    main_icon_copied = False
    for icon_path in main_icon_candidates:
        print(f"[INFO] Checking main icon candidate: {icon_path} (exists: {icon_path.exists()})")
        if icon_path.exists():
            try:
                dest_path = appdir / "mitotic-spindle-tool.png"
                shutil.copy(icon_path, dest_path)
                print(f"[SUCCESS] Copied main icon {icon_path.name} to AppImage root at {dest_path}")
                main_icon_copied = True
                break
            except Exception as e:
                print(f"[ERROR] Failed to copy main icon {icon_path.name}: {e}")
    
    if not icons_copied:
        print("[WARNING] No icons were copied to AppImage icon directories - application may not show proper icon in desktop environments")
    
    if not main_icon_copied:
        print("[WARNING] No main icon was copied to AppImage root - AppImage may not show proper icon")
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Type=Application
Name=Mitotic Spindle Tool
Comment=Image analysis tool for mitotic spindle analysis
Exec=mitotic-spindle-tool
Icon=mitotic-spindle-tool
Categories=Science;Education;
Terminal=false
StartupNotify=true
StartupWMClass=mitotic-spindle-tool
"""
    
    # Write desktop file to the standard location
    desktop_file_path = appdir / "usr/share/applications/mitotic-spindle-tool.desktop"
    with open(desktop_file_path, 'w') as f:
        f.write(desktop_content)
    print(f"[SUCCESS] Created desktop file at {desktop_file_path}")
    
    # Also write desktop file to AppDir root (required by AppImage)
    root_desktop_file_path = appdir / "mitotic-spindle-tool.desktop"
    with open(root_desktop_file_path, 'w') as f:
        f.write(desktop_content)
    print(f"[SUCCESS] Created root desktop file at {root_desktop_file_path}")
    
    # Create a DirIcon symlink pointing to the main icon (AppImage convention)
    diricon_path = appdir / ".DirIcon"
    main_icon_path = appdir / "mitotic-spindle-tool.png"
    if main_icon_path.exists() and not diricon_path.exists():
        try:
            os.symlink("mitotic-spindle-tool.png", diricon_path)
            print(f"[SUCCESS] Created .DirIcon symlink at {diricon_path}")
        except Exception as e:
            print(f"[WARNING] Failed to create .DirIcon symlink: {e}")
    
    # Also copy the icon with a more standard name for better compatibility
    if main_icon_path.exists():
        try:
            # Copy icon with application name for better recognition
            alt_icon_path = appdir / "mitotic_spindle_tool.png"
            shutil.copy(main_icon_path, alt_icon_path)
            print(f"[SUCCESS] Created alternative icon name at {alt_icon_path}")
        except Exception as e:
            print(f"[WARNING] Failed to create alternative icon: {e}")
    
    # Create AppRun
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/mitotic-spindle-tool" "$@"
"""
    
    apprun_path = appdir / "AppRun"
    with open(apprun_path, 'w') as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)
    
    # Create AppImage using absolute paths (no directory changes needed)
    try:
        # Make sure executable is executable
        target_executable_path = appdir / "usr/bin/mitotic-spindle-tool"
        if target_executable_path.exists():
            os.chmod(target_executable_path, 0o755)
        
        # Debug: List AppDir contents before creating AppImage
        print("[DEBUG] AppDir structure before creating AppImage:")
        if appdir.exists():
            for root, dirs, files in os.walk(appdir):
                level = root.replace(str(appdir), '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    file_path = Path(root) / file
                    print(f"{subindent}{file} ({file_path.stat().st_size} bytes)")
        
        # Run appimagetool with absolute paths (no need to change directories)
        print("Running appimagetool...")
        appimage_name = get_platform_appimage_name()
        appimage_path = DIST_DIR / appimage_name
        
        result = subprocess.run(
            ["appimagetool", "--verbose", str(appdir), str(appimage_path)], 
            env=env, 
            check=False, 
            capture_output=True, 
            text=True,
            cwd=str(root_dir)  # Run from root directory for consistency
        )
        # Print output for debugging
        if result.stdout:
            print(f"[INFO] appimagetool stdout: {result.stdout}")
        if result.stderr:
            print(f"[INFO] appimagetool stderr: {result.stderr}")
        
        print(f"[INFO] appimagetool exit code: {result.returncode}")
        
        if result.returncode == 0 and appimage_path.exists():
            os.chmod(appimage_path, 0o755)
            print(f"[SUCCESS] Created AppImage: {appimage_path}")
            
            # Test the AppImage to verify it was created correctly
            print("[INFO] Testing AppImage...")
            try:
                test_result = subprocess.run([str(appimage_path), "--help"], 
                                           capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    print("[SUCCESS] AppImage test passed")
                else:
                    print(f"[WARNING] AppImage test failed with exit code {test_result.returncode}")
                    if test_result.stderr:
                        print(f"[WARNING] AppImage test stderr: {test_result.stderr}")
            except subprocess.TimeoutExpired:
                print("[WARNING] AppImage test timed out (this may be normal in CI environments)")
            except Exception as e:
                print(f"[WARNING] AppImage test failed with exception: {e}")
            
            return appimage_path
        else:
            print(f"[WARNING] AppImage creation failed - appimagetool exit code: {result.returncode}")
            return None
            
    except Exception as e:
        print(f"[WARNING] AppImage creation failed with exception: {e}")
        return None

def prepare_icons():
    """Prepare and verify icons for the build process"""
    print("Preparing icons for build...")
    
    if not ICONS_DIR.exists():
        print("[WARNING] Icons directory not found, creating...")
        ICONS_DIR.mkdir(exist_ok=True)
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
        icon_path = ICONS_DIR / filename
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
