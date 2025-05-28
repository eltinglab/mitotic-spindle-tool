#!/usr/bin/env python3
"""
Enhanced DMG creation script for macOS with custom branding
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str), check=check, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    
    return result

def create_branded_dmg(executable_path, output_path):
    """Create a branded DMG with custom icon and layout"""
    
    if not Path(executable_path).exists():
        print(f"[ERROR] Executable not found: {executable_path}")
        return False
    
    # Create temporary directory for DMG contents
    dmg_temp_dir = Path("dist/dmg_temp")
    dmg_temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy executable
        app_name = "Mitotic Spindle Tool"
        shutil.copy2(executable_path, dmg_temp_dir / app_name)
        
        # Make executable
        os.chmod(dmg_temp_dir / app_name, 0o755)
        
        # Copy application icon if available
        icon_512 = Path("icons/EltingLabSpindle_512x512.png")
        if icon_512.exists():
            shutil.copy2(icon_512, dmg_temp_dir / ".VolumeIcon.icns")
        
        # Create Applications symlink for easy installation
        applications_link = dmg_temp_dir / "Applications"
        if not applications_link.exists():
            os.symlink("/Applications", applications_link)
        
        # Create README for the DMG
        readme_content = f"""# {app_name}

## Installation Instructions

1. Drag "{app_name}" to the Applications folder
2. Open Applications and double-click "{app_name}" to run

## About
This is the Mitotic Spindle Tool - an image analysis application for mitotic spindle analysis.

Developed by the Elting Lab.
"""
        
        with open(dmg_temp_dir / "README.txt", "w") as f:
            f.write(readme_content)
        
        # Create DMG with custom settings
        print("Creating DMG...")
        
        # First create a temporary DMG
        temp_dmg = Path("dist/temp.dmg")
        if temp_dmg.exists():
            temp_dmg.unlink()
            
        run_command([
            "hdiutil", "create",
            "-volname", "Mitotic Spindle Tool",
            "-srcfolder", str(dmg_temp_dir),
            "-ov", "-format", "UDRW",  # Read-write format for customization
            str(temp_dmg)
        ])
        
        # Mount the DMG for customization
        print("Mounting DMG for customization...")
        mount_result = run_command([
            "hdiutil", "attach", str(temp_dmg), "-mountpoint", "/Volumes/MitoticSpindleTool"
        ])
        
        try:
            # Set custom icon for the volume (requires macOS)
            if icon_512.exists():
                try:
                    # Convert PNG to icns
                    icns_path = dmg_temp_dir / "VolumeIcon.icns"
                    run_command([
                        "sips", "-s", "format", "icns", str(icon_512), "--out", str(icns_path)
                    ], check=False)
                    
                    # Copy icon to mounted volume
                    if icns_path.exists():
                        shutil.copy2(icns_path, "/Volumes/MitoticSpindleTool/.VolumeIcon.icns")
                        
                        # Set volume icon attribute
                        run_command([
                            "SetFile", "-a", "C", "/Volumes/MitoticSpindleTool"
                        ], check=False)
                        
                except subprocess.CalledProcessError:
                    print("[INFO] Could not set volume icon (optional)")
            
            # Set custom view options (requires AppleScript on macOS)
            applescript = f'''
            tell application "Finder"
                tell disk "Mitotic Spindle Tool"
                    open
                    set current view of container window to icon view
                    set toolbar visible of container window to false
                    set statusbar visible of container window to false
                    set the bounds of container window to {{100, 100, 600, 400}}
                    set arrangement of icon view options of container window to not arranged
                    set icon size of icon view options of container window to 128
                    set position of item "{app_name}" of container window to {{150, 200}}
                    set position of item "Applications" of container window to {{350, 200}}
                    close
                    open
                    update without registering applications
                    delay 2
                end tell
            end tell
            '''
            
            try:
                run_command(["osascript", "-e", applescript], check=False)
            except subprocess.CalledProcessError:
                print("[INFO] Could not set DMG layout (optional)")
            
        finally:
            # Unmount the DMG
            print("Unmounting DMG...")
            run_command(["hdiutil", "detach", "/Volumes/MitoticSpindleTool"], check=False)
        
        # Convert to final compressed DMG
        print("Creating final compressed DMG...")
        if Path(output_path).exists():
            Path(output_path).unlink()
            
        run_command([
            "hdiutil", "convert", str(temp_dmg),
            "-format", "UDZO",  # Compressed format
            "-o", str(output_path)
        ])
        
        # Clean up
        if temp_dmg.exists():
            temp_dmg.unlink()
        shutil.rmtree(dmg_temp_dir)
        
        print(f"[SUCCESS] Created branded DMG: {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] DMG creation failed: {e}")
        if dmg_temp_dir.exists():
            shutil.rmtree(dmg_temp_dir)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_dmg.py <executable_path> <output_dmg_path>")
        sys.exit(1)
    
    executable = sys.argv[1]
    output = sys.argv[2]
    
    success = create_branded_dmg(executable, output)
    sys.exit(0 if success else 1)
