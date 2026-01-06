import sys
import os
from config_manager import get_config_value

def setup_ai_engine():
    """
    Injects the correct library path (CPU or GPU) into sys.path
    BEFORE the library is imported.
    """
    # 1. Determine base path (Works for Dev and PyInstaller EXE)
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 2. Check Config
    use_gpu = get_config_value("use_gpu", False)
    
    # 3. Define Paths
    cpu_path = os.path.join(base_path, "assets", "engines", "cpu")
    gpu_path = os.path.join(base_path, "assets", "engines", "gpu")

    # 4. Injection Logic
    if use_gpu:
        print(f"BOOT: GPU Mode Enabled. Targeting: {gpu_path}")
        if os.path.exists(gpu_path):
            # Look here FIRST
            sys.path.insert(0, gpu_path)
            
            # Critical for Windows CUDA DLLs
            try:
                lib_path = os.path.join(gpu_path, "ctransformers", "lib")
                if os.path.exists(lib_path):
                    os.add_dll_directory(lib_path)
            except Exception:
                pass
            return True
        else:
            print("CRITICAL: GPU files not found. Fallback to CPU.")
            sys.path.insert(0, cpu_path)
            return False
    else:
        print(f"BOOT: CPU Mode Active. Targeting: {cpu_path}")
        sys.path.insert(0, cpu_path)
        return False
