# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the absolute path to the project root
# Simplified approach that works better in CI environments
import os
import sys

# Try multiple methods to find the project root
spec_root = None

# Method 1: Use environment variable if set by build script
if 'PYINSTALLER_ROOT_DIR' in os.environ:
    spec_root = os.environ['PYINSTALLER_ROOT_DIR']
    print(f"[SPEC] Using root from environment: {spec_root}")

# Method 2: Look for known project structure from current working directory
if not spec_root or not os.path.exists(os.path.join(spec_root, 'src', 'spindleGUI.py')):
    # Check current directory and parent directories
    current = os.getcwd()
    for _ in range(4):  # Check up to 4 levels up
        if os.path.exists(os.path.join(current, 'src', 'spindleGUI.py')):
            spec_root = current
            print(f"[SPEC] Found project root: {spec_root}")
            break
        parent = os.path.dirname(current)
        if parent == current:  # Reached filesystem root
            break
        current = parent

# Method 3: Try spec file path resolution as fallback
if not spec_root:
    try:
        if hasattr(sys, 'argv') and len(sys.argv) > 0:
            spec_file_path = os.path.abspath(sys.argv[0])
            if spec_file_path.endswith('.spec'):
                spec_dir = os.path.dirname(spec_file_path)
                potential_root = os.path.dirname(os.path.dirname(os.path.dirname(spec_dir)))
                if os.path.exists(os.path.join(potential_root, 'src', 'spindleGUI.py')):
                    spec_root = potential_root
                    print(f"[SPEC] Found root via spec file: {spec_root}")
    except Exception as e:
        print(f"[SPEC] Error in spec file path resolution: {e}")

# Final fallback
if not spec_root:
    spec_root = os.getcwd()
    print(f"[SPEC] Using fallback root: {spec_root}")

src_path = os.path.join(spec_root, 'src')
main_script = os.path.join(src_path, 'spindleGUI.py')
icon_path = os.path.join(spec_root, 'icons', 'EltingLabSpindle.ico')

# Add src to Python path to ensure modules can be found
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Ensure the main script exists
if not os.path.exists(main_script):
    raise FileNotFoundError(f"Main script not found: {main_script}")

# Print debug information
print(f"[SPEC] Project root: {spec_root}")
print(f"[SPEC] Source path: {src_path}")
print(f"[SPEC] Main script: {main_script}")
print(f"[SPEC] Icon path: {icon_path}")
print(f"[SPEC] Icons directory exists: {os.path.exists(os.path.join(spec_root, 'icons'))}")
print(f"[SPEC] Main script exists: {os.path.exists(main_script)}")

# List icons directory contents if it exists
icons_dir = os.path.join(spec_root, 'icons')
if os.path.exists(icons_dir):
    try:
        icons_list = os.listdir(icons_dir)
        print(f"[SPEC] Icons found: {icons_list}")
    except Exception as e:
        print(f"[SPEC] Error listing icons directory: {e}")
else:
    print(f"[SPEC] Icons directory not found at: {icons_dir}")

# Build the datas list with validation
datas_list = [
    # Include entire src directory as data files to ensure all modules are available
    (src_path, 'src'),
]

# Add icons directory if it exists
if os.path.exists(icons_dir):
    # Additional validation to ensure icons directory has content
    try:
        icons_contents = os.listdir(icons_dir)
        if icons_contents:
            datas_list.append((icons_dir, 'icons'))
            print(f"[SPEC] Added icons directory to PyInstaller data: {icons_dir} -> icons")
            print(f"[SPEC] Icons directory contains {len(icons_contents)} files: {icons_contents}")
        else:
            print(f"[SPEC] WARNING: Icons directory is empty: {icons_dir}")
    except Exception as e:
        print(f"[SPEC] ERROR: Cannot read icons directory {icons_dir}: {e}")
else:
    print(f"[SPEC] WARNING: Icons directory not found, skipping: {icons_dir}")
    # Debug: try to find where icons might actually be
    potential_locations = [
        os.path.join(os.getcwd(), 'icons'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'icons'),
        os.path.join(os.path.dirname(spec_root), 'icons'),
    ]
    for location in potential_locations:
        abs_location = os.path.abspath(location)
        if os.path.exists(abs_location):
            print(f"[SPEC] Found alternative icons directory: {abs_location}")
            try:
                alt_contents = os.listdir(abs_location)
                print(f"[SPEC] Alternative location contains: {alt_contents}")
            except:
                pass

a = Analysis(
    [main_script],
    pathex=[src_path, spec_root],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Include all custom modules
        'metadataDialog',
        'manualSpindleDialog', 
        'plotDialog',
        'plotSpindle',
        'curveFitData',
        'threshFunctions',
        'tiffFunctions',
        'version',
        'keypress_method',
        'spindlePreviewDialog',
        # Include common scientific computing modules that might be missed
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'PIL',
        'PIL.Image',
        'pkg_resources',
        'pkg_resources.py2_warn',
        'importlib.metadata',
        'importlib.metadata._compat',
        'importlib.metadata._functools',
        'importlib.metadata._itertools',
        'importlib.metadata._meta',
        'importlib.metadata._text',
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(os.path.dirname(os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else '.')), 'runtime_hook_src_modules.py')],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mitotic-spindle-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)
