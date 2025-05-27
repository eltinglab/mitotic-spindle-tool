@echo off
REM Build script for Windows packaging
REM This script creates PyInstaller executable for Windows

echo Building Mitotic Spindle Tool for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install build dependencies
echo Installing build tools...
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__
if exist "src\__pycache__" rmdir /s /q src\__pycache__

REM Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller mitotic-spindle-tool.spec

REM Check if build was successful
if exist "dist\mitotic-spindle-tool.exe" (
    echo PyInstaller build successful!
    
    REM Create a batch launcher
    echo @echo off > dist\run-mitotic-spindle-tool.bat
    echo cd /d "%%~dp0" >> dist\run-mitotic-spindle-tool.bat
    echo mitotic-spindle-tool.exe %%* >> dist\run-mitotic-spindle-tool.bat
    
    echo Created launcher script: dist\run-mitotic-spindle-tool.bat
) else (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

REM Create a zip distribution
echo Creating zip distribution...
powershell -command "Compress-Archive -Path 'dist\mitotic-spindle-tool.exe', 'dist\run-mitotic-spindle-tool.bat' -DestinationPath 'dist\mitotic-spindle-tool-windows.zip' -Force"

echo Build completed successfully!
echo Outputs:
echo   - Executable: dist\mitotic-spindle-tool.exe
echo   - Launcher: dist\run-mitotic-spindle-tool.bat
echo   - Zip package: dist\mitotic-spindle-tool-windows.zip
echo.
echo To run the application:
echo   dist\mitotic-spindle-tool.exe
echo or
echo   dist\run-mitotic-spindle-tool.bat

pause
