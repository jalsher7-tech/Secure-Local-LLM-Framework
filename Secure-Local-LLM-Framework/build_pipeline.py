# build_ultimate.py
import sys
import subprocess
import os

def build():
    print("--- OPSGUARD FINAL BUILD (Surgical OneFile) ---")
    print("Goal: OneFile | Console Hidden | Engines Fixed | Junk Removed")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(project_dir, "assets")
    
    # 1. THE BASE COMMAND
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile", 
        "--enable-plugin=pyqt6",
        
        # --- AESTHETICS ---
        # I have enabled the console Disable flag. 
        # If this crashes silently, we know it's a runtime error, not a build error.
        "--windows-disable-console", 
        "--windows-icon-from-ico=assets/Cyphie.ico",
        "--include-data-files=Splash.png=Splash.png",
        
        # --- CORE SETTINGS ---
        "--nofollow-import-to=ctransformers", # Don't compile AI engine (Keep it dynamic)
        
        # --- DEPENDENCIES (All the ones we found) ---
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

    # 2. STANDARD ASSETS (Safe Folders)
    # These folders contain images/gifs. Nuitka handles these fine.
    safe_folders = ["idle", "thinking", "responding", "model"]
    for folder in safe_folders:
        src = os.path.join(assets_dir, folder)
        dst = f"assets/{folder}"
        if os.path.exists(src):
            cmd.append(f"--include-data-dir={src}={dst}")

    # 3. STANDARD FILES
    files = ["Cyphie.ico", "tinyllama.gguf"]
    for f in files:
        src = os.path.join(assets_dir, f)
        dst = f"assets/{f}"
        if os.path.exists(src):
            cmd.append(f"--include-data-files={src}={dst}")

    # 4. SURGICAL ENGINE LOADER (The Fix)
    # We manually find every important file in the engines folder
    # and force-feed it to Nuitka as a DATA FILE.
    
    print("\nScanning Engines & Filtering Junk...")
    
    engines_path = os.path.join(assets_dir, "engines")
    
    # Files to ignore to prevent "Command Too Long" errors
    ignore_extensions = [".pyc", ".dist-info", ".git"]
    ignore_folders = ["__pycache__", ".ipynb_checkpoints"]

    for root, dirs, filenames in os.walk(engines_path):
        # Filter out junk directories in-place
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        for filename in filenames:
            # Filter out junk files
            if any(filename.endswith(ext) for ext in ignore_extensions):
                continue
                
            # Full path on disk
            abs_src = os.path.join(root, filename)
            
            # Relative path inside the EXE (must start with assets/...)
            rel_path = os.path.relpath(abs_src, project_dir)
            rel_path = rel_path.replace("\\", "/") # Normalize for Windows
            
            # THE MAGIC FLAG: Treat DLLs and PY files as raw data
            flag = f"--include-data-files={abs_src}={rel_path}"
            cmd.append(flag)
            
            # Visual check for you
            if filename.endswith(".dll") or filename == "__init__.py":
                print(f"  + Locked: {rel_path}")

    cmd.append("main.py")

    print("\nStarting Compilation... (Grab a coffee, this takes ~3-5 mins)")
    try:
        subprocess.check_call(cmd)
        print("\nSUCCESS! Your final file is at 'dist/main.exe'")
    except subprocess.CalledProcessError:
        print("\nCompilation Failed.")

if __name__ == "__main__":
    build()
