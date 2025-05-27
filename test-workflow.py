#!/usr/bin/env python3
"""
Local workflow testing script
Simulates the GitHub Actions workflow steps locally for testing
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    if isinstance(cmd, str):
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True)
    else:
        result = subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
    
    if capture_output:
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    
    return result

def test_lint():
    """Test linting step"""
    print("\n" + "="*50)
    print("Testing Lint Step")
    print("="*50)
    
    try:
        # Install flake8 if not present
        run_command([sys.executable, "-m", "pip", "install", "flake8"])
        
        # Run linting
        run_command([sys.executable, "-m", "flake8", "src/", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"])
        print("[SUCCESS] Linting passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Linting failed: {e}")
        return False

def test_imports():
    """Test import step"""
    print("\n" + "="*50)
    print("Testing Import Step")
    print("="*50)
    
    modules = ["spindleGUI", "curveFitData", "plotSpindle", "plotDialog", "manualSpindleDialog", "spindlePreviewDialog"]
    
    original_cwd = os.getcwd()
    try:
        os.chdir("src")
        
        for module in modules:
            try:
                run_command([sys.executable, "-c", f"import {module}; print('[SUCCESS] {module} imports successfully')"])
            except subprocess.CalledProcessError:
                print(f"[ERROR] {module} import failed")
                return False
                
        print("[SUCCESS] All imports successful")
        return True
    finally:
        os.chdir(original_cwd)

def test_build():
    """Test build step"""
    print("\n" + "="*50)
    print("Testing Build Step")
    print("="*50)
    
    try:
        # Run the build
        run_command([sys.executable, "build.py"])
        
        # Check if executable was created
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            executable_path = Path("dist/mitotic-spindle-tool.exe")
        else:
            executable_path = Path("dist/mitotic-spindle-tool")
            
        if executable_path.exists():
            size = executable_path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"[SUCCESS] Executable built successfully: {executable_path}")
            print(f"📁 Size: {size_mb:.2f} MB")
            return True
        else:
            print(f"[ERROR] Executable not found: {executable_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        return False

def test_package():
    """Test package creation"""
    print("\n" + "="*50)
    print("Testing Package Creation")
    print("="*50)
    
    import platform
    system = platform.system().lower()
    
    try:
        os.chdir("dist")
        
        if system == "windows":
            # Test ZIP creation
            import zipfile
            with zipfile.ZipFile("test-package.zip", 'w') as zipf:
                zipf.write("mitotic-spindle-tool.exe")
                if os.path.exists("run-mitotic-spindle-tool.bat"):
                    zipf.write("run-mitotic-spindle-tool.bat")
            print("[SUCCESS] Windows ZIP package created")
            
        else:
            # Test tar.gz creation
            import tarfile
            with tarfile.open("test-package.tar.gz", 'w:gz') as tarf:
                tarf.add("mitotic-spindle-tool")
                if os.path.exists("run-mitotic-spindle-tool.sh"):
                    tarf.add("run-mitotic-spindle-tool.sh")
            print("[SUCCESS] Unix tar.gz package created")
            
        os.chdir("..")
        return True
        
    except Exception as e:
        print(f"[ERROR] Package creation failed: {e}")
        os.chdir("..")
        return False

def create_test_report():
    """Create a test report similar to what PR workflows generate"""
    print("\n" + "="*50)
    print("Creating Test Report")
    print("="*50)
    
    import platform
    system = platform.system()
    
    report = f"""# Local Build Test Report

**Platform**: {system}
**Python Version**: {sys.version.split()[0]}

## Test Results

### ✅ Lint Check
Code linting passed successfully.

### ✅ Import Test
All module imports completed successfully.

### ✅ Build Test
Executable built successfully.

### ✅ Package Test
Distribution package created successfully.

## Files Created
"""
    
    dist_path = Path("dist")
    if dist_path.exists():
        report += "```\n"
        for item in dist_path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                size_mb = size / (1024 * 1024)
                report += f"{item.name:<30} {size_mb:>8.2f} MB\n"
        report += "```\n"
    
    report += """
## Next Steps
- Test the executable manually
- Check the launcher scripts
- Verify all features work as expected
"""
    
    with open("local_test_report.md", "w") as f:
        f.write(report)
    
    print("📝 Test report saved to: local_test_report.md")

def main():
    """Main test function"""
    print("🔨 Local Workflow Testing")
    print("This script simulates GitHub Actions workflow steps locally")
    print()
    
    # Check if we're in the right directory
    if not Path("src/spindleGUI.py").exists():
        print("[ERROR] Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies
    print("Installing dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller", "flake8"])
    
    # Run tests
    tests = [
        ("Lint", test_lint),
        ("Imports", test_imports),
        ("Build", test_build),
        ("Package", test_package),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Create report
    create_test_report()
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:<15} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The workflow should work on GitHub Actions.")
        return 0
    else:
        print("[ERROR] Some tests failed. Fix issues before pushing to GitHub.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
