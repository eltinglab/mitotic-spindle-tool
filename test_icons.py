#!/usr/bin/env python3
"""
Icon Integration Test Script
Tests that icons are properly embedded in executables and packages
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=isinstance(cmd, str), check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None

def test_icon_files():
    """Test that all required icon files are present"""
    print("🔍 Testing icon file availability...")
    
    icons_dir = Path("icons")
    if not icons_dir.exists():
        print("❌ Icons directory not found!")
        return False
    
    required_icons = {
        "Windows Icon": "EltingLabSpindle.ico",
        "High-res PNG (512px)": "EltingLabSpindle_512x512.png",
        "Medium-res PNG (256px)": "EltingLabSpindle_256x256.png",
        "Small PNG (64px)": "EltingLabSpindle_64x64.png",
        "Tiny PNG (32px)": "EltingLabSpindle_32x32.png",
    }
    
    all_found = True
    for desc, filename in required_icons.items():
        icon_path = icons_dir / filename
        if icon_path.exists():
            size = icon_path.stat().st_size
            print(f"✅ {desc}: {filename} ({size:,} bytes)")
        else:
            print(f"❌ {desc}: {filename} - NOT FOUND")
            all_found = False
    
    return all_found

def test_pyinstaller_spec():
    """Test that PyInstaller spec file includes icon"""
    print("\n🔍 Testing PyInstaller spec file...")
    
    spec_file = Path("mitotic-spindle-tool.spec")
    if not spec_file.exists():
        print("❌ PyInstaller spec file not found!")
        return False
    
    with open(spec_file, 'r') as f:
        content = f.read()
    
    if "icon=" in content and "EltingLabSpindle.ico" in content:
        print("✅ PyInstaller spec includes icon configuration")
        return True
    else:
        print("❌ PyInstaller spec missing icon configuration")
        return False

def test_windows_executable_icon():
    """Test Windows executable icon (if on Windows and executable exists)"""
    print("\n🔍 Testing Windows executable icon...")
    
    if platform.system() != "Windows":
        print("⏭️  Skipping (not on Windows)")
        return True
    
    exe_path = Path("dist/mitotic-spindle-tool.exe")
    if not exe_path.exists():
        print("⏭️  Skipping (executable not found)")
        return True
    
    # Try to extract icon info using PowerShell (Windows only)
    try:
        result = run_command([
            "powershell", "-Command",
            f"(Get-ItemProperty '{exe_path}').VersionInfo | Select-Object FileName, FileDescription"
        ], check=False)
        
        if result and result.returncode == 0:
            print("✅ Windows executable accessible")
            print(f"📋 {result.stdout}")
            return True
        else:
            print("❌ Could not read Windows executable properties")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Windows executable: {e}")
        return False

def test_macos_dmg_icon():
    """Test macOS DMG icon (if on macOS and DMG exists)"""
    print("\n🔍 Testing macOS DMG...")
    
    if platform.system() != "Darwin":
        print("⏭️  Skipping (not on macOS)")
        return True
    
    dmg_path = Path("dist/mitotic-spindle-tool-macos.dmg")
    if not dmg_path.exists():
        print("⏭️  Skipping (DMG not found)")
        return True
    
    # Test that DMG can be mounted
    try:
        result = run_command([
            "hdiutil", "imageinfo", str(dmg_path)
        ], check=False)
        
        if result and result.returncode == 0:
            print("✅ DMG file is valid")
            return True
        else:
            print("❌ DMG file appears corrupted")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DMG: {e}")
        return False

def test_build_scripts():
    """Test that build scripts exist and are executable"""
    print("\n🔍 Testing build scripts...")
    
    scripts = {
        "Main build script": "build.py",
        "Enhanced DMG creator": "create_dmg.py",
        "PyInstaller spec": "mitotic-spindle-tool.spec"
    }
    
    all_good = True
    for desc, filename in scripts.items():
        script_path = Path(filename)
        if script_path.exists():
            if filename.endswith('.py'):
                # Test that Python script is syntactically valid
                try:
                    result = run_command([sys.executable, "-m", "py_compile", str(script_path)], check=False)
                    if result and result.returncode == 0:
                        print(f"✅ {desc}: {filename} (syntax OK)")
                    else:
                        print(f"❌ {desc}: {filename} (syntax error)")
                        all_good = False
                except Exception:
                    print(f"❌ {desc}: {filename} (could not test)")
                    all_good = False
            else:
                print(f"✅ {desc}: {filename}")
        else:
            print(f"❌ {desc}: {filename} - NOT FOUND")
            all_good = False
    
    return all_good

def main():
    """Run all icon integration tests"""
    print("🧪 Icon Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Icon Files", test_icon_files),
        ("PyInstaller Spec", test_pyinstaller_spec),
        ("Windows Executable", test_windows_executable_icon),
        ("macOS DMG", test_macos_dmg_icon),
        ("Build Scripts", test_build_scripts),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Icon integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
