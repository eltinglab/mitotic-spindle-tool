# PyInstaller runtime hook to ensure src modules are importable
import sys
import os

# Get the directory where the executable is running
if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    src_dir = os.path.join(bundle_dir, 'src')
    
    # Add src directory to Python path if it exists
    if os.path.exists(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"[RUNTIME] Added {src_dir} to Python path")
    else:
        print(f"[RUNTIME] Warning: src directory not found at {src_dir}")
        
    # Also try adding the bundle directory itself
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
        print(f"[RUNTIME] Added {bundle_dir} to Python path")
        
    # List available modules for debugging
    try:
        import importlib.util
        modules_to_check = [
            'metadataDialog', 'manualSpindleDialog', 'plotDialog',
            'plotSpindle', 'curveFitData', 'threshFunctions', 
            'tiffFunctions', 'version', 'keypress_method', 
            'spindlePreviewDialog'
        ]
        
        for module_name in modules_to_check:
            spec = importlib.util.find_spec(module_name)
            if spec:
                print(f"[RUNTIME] Found module: {module_name} at {spec.origin}")
            else:
                print(f"[RUNTIME] Missing module: {module_name}")
                
    except Exception as e:
        print(f"[RUNTIME] Error checking modules: {e}")
