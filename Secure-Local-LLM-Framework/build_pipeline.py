# build_pipeline.py
import sys
import subprocess
import os
import shutil

def build():
    print("--- OPSGUARD FINAL BUILD (MinGW64 Static) ---")
    print("Goal: Create a standalone EXE that works on fresh Windows installs.")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(project_dir, "assets")
    
    # --- STEP 1: PRE-STAGE DLLS (Safety Net) ---
    # We copy the DLLs to the root so they are bundled INSIDE the app
    # for the AI engine to use later.
    print("\n[1/3] Staging VCRUNTIME for internal use...")
    python_dir = os.path.dirname(sys.executable)
    critical_dlls = ["vcruntime140.dll", "msvcp140.dll", "vcruntime140_1.dll"]
    copied_files = []

    for dll in critical_dlls:
        src = os.path.join(python_dir, dll)
        if not os.path.exists(src):
            src = os.path.join("C:\\Windows\\System32", dll)
        
        if os.path.exists(src):
            dst = os.path.join(project_dir, dll)
            try:
                shutil.copy2(src, dst)
                copied_files.append(dst)
            except:
                pass

    # --- STEP 2: BUILD COMMAND ---
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile", 
        "--enable-plugin=pyqt6",
        
        # *** THE SOLUTION ***
        # This tells Nuitka to use the MinGW compiler.
        # This creates a bootloader that DOES NOT require VCRUNTIME installed on the PC.
        "--mingw64",
        
        # Aesthetics
        "--windows-disable-console", 
        "--windows-icon-from-ico=assets/Cyphie.ico",
        "--include-data-files=Splash.png=Splash.png",
        
        # Core
        "--nofollow-import-to=ctransformers", 
        
        # Dependencies
        "--include-package=huggingface_hub",
        "--include-package=tqdm",
        "--include-package=requests",
        "--include-package=regex",
        "--include-package=cpuinfo",
        "--include-package=filelock",
        "--include-package=cryptography",
        "--include-package=vosk",
        "--include-package=pyaudio",
        
        "--output-dir=dist",
    ]

    # Assets
    safe_folders = ["idle", "thinking", "responding", "model"]
    for folder in safe_folders:
        src = os.path.join(assets_dir, folder)
        dst = f"assets/{folder}"
        if os.path.exists(src):
            cmd.append(f"--include-data-dir={src}={dst}")

    # Files
    files = ["Cyphie.ico", "tinyllama.gguf"]
    for f in files:
        src = os.path.join(assets_dir, f)
        dst = f"assets/{f}"
        if os.path.exists(src):
            cmd.append(f"--include-data-files={src}={dst}")

    # Engines
    print("\n[2/3] Configuring Engine Paths...")
    engines_path = os.path.join(assets_dir, "engines")
    ignore_extensions = [".pyc", ".dist-info", ".git"]
    ignore_folders = ["__pycache__", ".ipynb_checkpoints"]

    for root, dirs, filenames in os.walk(engines_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        for filename in filenames:
            if any(filename.endswith(ext) for ext in ignore_extensions):
                continue
            abs_src = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_src, project_dir).replace("\\", "/")
            cmd.append(f"--include-data-files={abs_src}={rel_path}")

    cmd.append("main.py")

    print("\n[3/3] Starting Compilation...")
    print("NOTE: If asked to download MinGW64, please type YES.")
    try:
        subprocess.check_call(cmd)
        print("\nSUCCESS! Your final file is at 'dist/main.exe'")
    except subprocess.CalledProcessError:
        print("\nCompilation Failed.")
    finally:
        # Cleanup the temporary DLL copies
        for f in copied_files:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass

if __name__ == "__main__":
    build()
