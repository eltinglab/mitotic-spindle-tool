# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the absolute path to the project root
# In PyInstaller spec files, we need to use sys.argv[0] to get the spec file path
# because __file__ is not available in the exec context
spec_file_path = os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else '.')
if spec_file_path.endswith('.spec'):
    # We're running from the spec file, calculate paths relative to it
    spec_dir = os.path.dirname(spec_file_path)
    spec_root = os.path.dirname(os.path.dirname(os.path.dirname(spec_dir)))
else:
    # Fallback: assume we're in the project root
    spec_root = os.getcwd()

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

a = Analysis(
    [main_script],
    pathex=[src_path, spec_root],
    binaries=[],
    datas=[
        # Include entire src directory as data files to ensure all modules are available
        (src_path, 'src'),
    ],
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
