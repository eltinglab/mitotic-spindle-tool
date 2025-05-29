#!/usr/bin/env python3
"""
Version management script for Mitotic Spindle Tool

This script updates the version in the central version.py file and 
synchronizes it to pyproject.toml for compatibility.

Usage:
    python update_version.py 1.2.0
    python update_version.py --bump patch
    python update_version.py --bump minor  
    python update_version.py --bump major
"""

import sys
import os
import re
from pathlib import Path

def get_current_version():
    """Get current version from version.py"""
    version_file = Path("../../src/version.py")
    if not version_file.exists():
        return "1.0.0"
    
    with open(version_file, 'r') as f:
        content = f.read()
    
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    
    return "1.0.0"

def bump_version(current_version, bump_type):
    """Bump version according to semantic versioning"""
    parts = list(map(int, current_version.split('.')))
    
    if bump_type == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    elif bump_type == "minor":
        parts[1] += 1
        parts[2] = 0
    elif bump_type == "patch":
        parts[2] += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return ".".join(map(str, parts))

def update_version_file(new_version):
    """Update the central version.py file"""
    version_file = Path("src/version.py")
    
    content = f'''"""
Version information for Mitotic Spindle Tool

This is the single source of truth for version information.
All other files should import from here.
"""

__version__ = "{new_version}"
__version_info__ = tuple(map(int, __version__.split('.')))

# For display purposes (with 'v' prefix)
VERSION_DISPLAY = f"v{{__version__}}"

# For compatibility with older code
version = __version__'''
    
    with open(version_file, 'w') as f:
        f.write(content)

def update_pyproject_toml(new_version):
    """Update pyproject.toml for compatibility"""
    pyproject_file = Path("../../pyproject.toml")
    
    if not pyproject_file.exists():
        return
    
    with open(pyproject_file, 'r') as f:
        content = f.read()
    
    # Update version line
    content = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']',
        f'version = "{new_version}"',
        content
    )
    
    with open(pyproject_file, 'w') as f:
        f.write(content)

def main():
    if len(sys.argv) < 2:
        current = get_current_version()
        print(f"Current version: {current}")
        print("\nUsage:")
        print(f"  {sys.argv[0]} 1.2.0                 # Set specific version")
        print(f"  {sys.argv[0]} --bump patch          # Bump patch version")
        print(f"  {sys.argv[0]} --bump minor          # Bump minor version") 
        print(f"  {sys.argv[0]} --bump major          # Bump major version")
        return 1
    
    current_version = get_current_version()
    
    if sys.argv[1] == "--bump":
        if len(sys.argv) < 3:
            print("Error: --bump requires a bump type (patch, minor, major)")
            return 1
        
        bump_type = sys.argv[2]
        new_version = bump_version(current_version, bump_type)
        print(f"Bumping {bump_type} version: {current_version} → {new_version}")
        
    else:
        new_version = sys.argv[1]
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print(f"Error: Invalid version format '{new_version}'. Use semantic versioning (e.g., 1.2.3)")
            return 1
        
        print(f"Setting version: {current_version} → {new_version}")
    
    # Update files
    update_version_file(new_version)
    update_pyproject_toml(new_version)
    
    print(f"✅ Version updated to {new_version}")
    print("Files updated:")
    print("  - src/version.py")
    print("  - pyproject.toml")
    print("\nNote: setup.py will automatically use the new version when imported")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
