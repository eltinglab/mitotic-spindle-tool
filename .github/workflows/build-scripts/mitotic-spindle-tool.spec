# -*- mode: python ; coding: utf-8 -*-
import os

# Get the absolute path to the project root from this spec file location
spec_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(spec_root, 'src')
main_script = os.path.join(src_path, 'spindleGUI.py')
icon_path = os.path.join(spec_root, 'icons', 'EltingLabSpindle.ico')

a = Analysis(
    [main_script],
    pathex=[src_path, spec_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        'metadataDialog',
        'manualSpindleDialog', 
        'plotDialog',
        'plotSpindle',
        'curveFitData',
        'threshFunctions',
        'tiffFunctions',
        'version',
        'keypress_method',
        'spindlePreviewDialog'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    icon=icon_path,
)
