#!/bin/bash

# Build script for Linux packaging
# This script creates both PyInstaller binaries and DEB/RPM packages

set -e  # Exit on any error

echo "Building Mitotic Spindle Tool for Linux..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt

# Install build dependencies
print_status "Installing build tools..."
pip install pyinstaller cx_Freeze

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.spec __pycache__/ src/__pycache__/

# Build with PyInstaller
print_status "Building executable with PyInstaller..."
pyinstaller mitotic-spindle-tool.spec

# Check if build was successful
if [ -f "dist/mitotic-spindle-tool" ]; then
    print_status "PyInstaller build successful!"
    
    # Make executable
    chmod +x dist/mitotic-spindle-tool
    
    # Create a simple launcher script
    cat > dist/run-mitotic-spindle-tool.sh << 'EOF'
#!/bin/bash
# Launcher script for Mitotic Spindle Tool

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the application
./mitotic-spindle-tool "$@"
EOF
    
    chmod +x dist/run-mitotic-spindle-tool.sh
    
    print_status "Created launcher script: dist/run-mitotic-spindle-tool.sh"
else
    print_error "PyInstaller build failed!"
    exit 1
fi

# Create AppImage (if appimagetool is available)
if command -v appimagetool &> /dev/null; then
    print_status "Creating AppImage..."
    
    # Create AppDir structure
    mkdir -p dist/AppDir/usr/bin
    mkdir -p dist/AppDir/usr/share/applications
    mkdir -p dist/AppDir/usr/share/icons/hicolor/256x256/apps
    
    # Copy executable
    cp dist/mitotic-spindle-tool dist/AppDir/usr/bin/
    
    # Create desktop file
    cat > dist/AppDir/usr/share/applications/mitotic-spindle-tool.desktop << EOF
[Desktop Entry]
Type=Application
Name=Mitotic Spindle Tool
Comment=Image analysis tool for mitotic spindle analysis
Exec=mitotic-spindle-tool
Icon=mitotic-spindle-tool
Categories=Science;Education;
Terminal=false
EOF
    
    # Create a simple icon (if you have one, replace this)
    # For now, we'll skip the icon or use a default one
    
    # Create AppRun
    cat > dist/AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/mitotic-spindle-tool" "$@"
EOF
    chmod +x dist/AppDir/AppRun
    
    # Create the AppImage
    cd dist
    appimagetool AppDir mitotic-spindle-tool.AppImage
    cd ..
    
    if [ -f "dist/mitotic-spindle-tool.AppImage" ]; then
        print_status "AppImage created successfully!"
        chmod +x dist/mitotic-spindle-tool.AppImage
    fi
fi

# Create a simple tarball distribution
print_status "Creating tarball distribution..."
cd dist
tar -czf mitotic-spindle-tool-linux.tar.gz mitotic-spindle-tool run-mitotic-spindle-tool.sh
cd ..

print_status "Build completed successfully!"
print_status "Outputs:"
print_status "  - Executable: dist/mitotic-spindle-tool"
print_status "  - Launcher: dist/run-mitotic-spindle-tool.sh"
print_status "  - Tarball: dist/mitotic-spindle-tool-linux.tar.gz"

if [ -f "dist/mitotic-spindle-tool.AppImage" ]; then
    print_status "  - AppImage: dist/mitotic-spindle-tool.AppImage"
fi

print_status ""
print_status "To run the application:"
print_status "  ./dist/mitotic-spindle-tool"
print_status "or"
print_status "  ./dist/run-mitotic-spindle-tool.sh"

if [ -f "dist/mitotic-spindle-tool.AppImage" ]; then
    print_status "or"
    print_status "  ./dist/mitotic-spindle-tool.AppImage"
fi
