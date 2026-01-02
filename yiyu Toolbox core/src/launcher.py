import os
import sys
import subprocess

def launch():
    # Get current directory
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
    
    # Paths relative to the launcher EXE
    runtime_python = os.path.join(base_dir, "runtime", "Scripts", "pythonw.exe")
    demo_script = os.path.join(base_dir, "src", "demo.py")
    
    # Environment Fixes (Qt & OpenMP)
    env = os.environ.copy()
    env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    # Auto-locate Qt plugins
    pyqt_plugin_base = os.path.join(base_dir, "runtime", "Lib", "site-packages", "PyQt5", "Qt5", "plugins")
    if not os.path.exists(pyqt_plugin_base):
        pyqt_plugin_base = os.path.join(base_dir, "runtime", "Lib", "site-packages", "PyQt5", "Qt", "plugins")
        
    if os.path.exists(os.path.join(pyqt_plugin_base, "platforms")):
        env['QT_QPA_PLATFORM_PLUGIN_PATH'] = pyqt_plugin_base

    # Launch the main app
    if os.path.exists(runtime_python) and os.path.exists(demo_script):
        subprocess.Popen([runtime_python, demo_script], env=env, cwd=base_dir)
    else:
        # Fallback for debugging
        print(f"Error: Missing components.\nPython: {runtime_python}\nScript: {demo_script}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    launch()
