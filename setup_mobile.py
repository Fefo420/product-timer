import os
import sys
import subprocess
import platform
import shutil
import venv

VENV_NAME = "mobile_env"

def get_venv_executable(name):
    """Returns the path to an executable inside the venv (cross-platform)."""
    if platform.system() == "Windows":
        return os.path.abspath(os.path.join(VENV_NAME, "Scripts", f"{name}.exe"))
    else:
        return os.path.abspath(os.path.join(VENV_NAME, "bin", name))

def check_system_deps():
    """Checks for Arch Linux and Debian dependencies needed for Flet."""
    if platform.system() != "Linux":
        return

    print("🐧 Linux detected. Checking system display drivers...")
    
    is_arch = os.path.exists("/etc/arch-release")
    
    if is_arch:
        print("💡 ARCH USER DETECTED. If the app fails to open, run:")
        print("   sudo pacman -S gtk3 gst-plugins-good python")
    else:
        print("💡 DEBIAN/UBUNTU USER DETECTED. Run if needed:")
        print("   sudo apt install libgtk-3-0 libgst-full-1.0")

def setup_virtual_env():
    """Creates the virtual environment if it doesn't exist."""
    python_exe = get_venv_executable("python")
    
    # Self-healing: Remove broken venv
    if os.path.exists(VENV_NAME) and not os.path.exists(python_exe):
        print("🧹 Removing broken virtual environment...")
        shutil.rmtree(VENV_NAME)
    
    if not os.path.exists(VENV_NAME):
        print(f"📦 Creating virtual environment '{VENV_NAME}'...")
        try:
            venv.create(VENV_NAME, with_pip=True)
            print("✅ Virtual environment created.")
        except Exception as e:
            print(f"❌ Failed to create venv: {e}")
            sys.exit(1)

def setup_python_deps():
    """Installs all required Python libraries inside the venv."""
    print("🔍 Installing Python libraries in virtual environment...")
    required = ["flet", "requests", "packaging"]
    
    pip_exe = get_venv_executable("pip")
    
    try:
        subprocess.check_call([pip_exe, "install"] + required)
        print("✅ Python libraries ready.")
    except Exception as e:
        print(f"❌ Failed to install libraries: {e}")
        sys.exit(1)

def run_mobile_test():
    """Launches the mobile app using the venv's Python."""
    env = os.environ.copy()
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = root_dir + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = root_dir

    mobile_script = os.path.join("mobile", "main.py")
    
    if not os.path.exists(mobile_script):
        print(f"❌ Error: Could not find {mobile_script}")
        return

    # Use the venv's Python, not system Python
    python_exe = get_venv_executable("python")
    
    print(f"🚀 Launching Mobile App from {mobile_script}...")
    try:
        subprocess.run([python_exe, mobile_script], env=env)
    except KeyboardInterrupt:
        print("\n🛑 App closed.")

if __name__ == "__main__":
    print("=== FOCUS STATION MOBILE SETUP & TEST ===")
    check_system_deps()
    setup_virtual_env()    # NEW: Create venv first
    setup_python_deps()     # Install into venv
    run_mobile_test()       # Run using venv's python