#!/usr/bin/env python3
"""
Generate build metadata and checksums for release verification.
This script creates checksums and build information for release artifacts.
"""

import os
import sys
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for version import
sys.path.insert(0, 'src')
try:
    from version import __version__, VERSION_DISPLAY
except ImportError:
    print("Warning: Could not import version info from src/version.py")
    __version__ = "unknown"
    VERSION_DISPLAY = "unknown"


def calculate_checksum(file_path, algorithm='sha256'):
    """Calculate checksum for a file."""
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except FileNotFoundError:
        return None


def get_file_size(file_path):
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except FileNotFoundError:
        return None


def generate_metadata(dist_dir="dist"):
    """Generate build metadata for all artifacts in dist directory."""
    
    dist_path = Path(dist_dir)
    if not dist_path.exists():
        print(f"Error: Distribution directory '{dist_dir}' not found")
        return None
    
    # Common artifact patterns
    artifacts = [
        "mitotic-spindle-tool.exe",
        "mitotic-spindle-tool",
        "mitotic-spindle-tool.AppImage",
        "mitotic-spindle-tool-linux.tar.gz",
        "mitotic-spindle-tool-macos.tar.gz",
        "mitotic-spindle-tool-macos.dmg",
        "run-mitotic-spindle-tool.sh"
    ]
    
    metadata = {
        "build_info": {
            "version": __version__,
            "version_display": VERSION_DISPLAY,
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.machine()
        },
        "artifacts": {}
    }
    
    # Process all files in dist directory
    for file_path in dist_path.iterdir():
        if file_path.is_file():
            filename = file_path.name
            
            file_info = {
                "filename": filename,
                "size_bytes": get_file_size(file_path),
                "sha256": calculate_checksum(file_path, 'sha256'),
                "md5": calculate_checksum(file_path, 'md5')
            }
            
            # Only include if we successfully got checksums
            if file_info["sha256"] and file_info["md5"]:
                metadata["artifacts"][filename] = file_info
                print(f"✓ Processed {filename} ({file_info['size_bytes']} bytes)")
            else:
                print(f"⚠ Skipped {filename} (could not read)")
    
    return metadata


def save_metadata(metadata, output_file="build_metadata.json"):
    """Save metadata to JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2, sort_keys=True)
        print(f"✓ Metadata saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving metadata: {e}")
        return False


def generate_checksums_text(metadata, output_file="CHECKSUMS.txt"):
    """Generate human-readable checksums file."""
    try:
        with open(output_file, 'w') as f:
            f.write(f"# Mitotic Spindle Tool v{metadata['build_info']['version']} - Checksums\n")
            f.write(f"# Generated: {metadata['build_info']['build_timestamp']}\n")
            f.write(f"# Platform: {metadata['build_info']['platform']}\n\n")
            
            for filename, info in sorted(metadata['artifacts'].items()):
                f.write(f"## {filename}\n")
                f.write(f"Size: {info['size_bytes']:,} bytes\n")
                f.write(f"SHA256: {info['sha256']}\n")
                f.write(f"MD5: {info['md5']}\n\n")
        
        print(f"✓ Checksums saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving checksums: {e}")
        return False


def main():
    """Main function."""
    print("🔧 Generating build metadata and checksums...")
    print(f"Version: {VERSION_DISPLAY}")
    
    # Generate metadata
    metadata = generate_metadata()
    if not metadata:
        sys.exit(1)
    
    if not metadata["artifacts"]:
        print("⚠ No artifacts found in dist directory")
        sys.exit(1)
    
    # Save metadata files
    success = True
    success &= save_metadata(metadata, "dist/build_metadata.json")
    success &= generate_checksums_text(metadata, "dist/CHECKSUMS.txt")
    
    if success:
        print(f"✅ Generated metadata for {len(metadata['artifacts'])} artifacts")
        
        # Print summary
        total_size = sum(info['size_bytes'] for info in metadata['artifacts'].values())
        print(f"📊 Total artifacts size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        
        # Print artifact list
        print("\n📦 Artifacts:")
        for filename, info in sorted(metadata['artifacts'].items()):
            size_mb = info['size_bytes'] / 1024 / 1024
            print(f"  • {filename} ({size_mb:.1f} MB)")
    else:
        print("❌ Failed to generate metadata")
        sys.exit(1)


if __name__ == "__main__":
    main()
