import os
import sys
import subprocess
import platform
import shutil

def check_system_deps():
    """Checks for Arch Linux and Debian dependencies needed for Flet."""
    if platform.system() != "Linux":
        return

    print("🐧 Linux detected. Checking system display drivers...")
    
    # Check for Arch specifically
    is_arch = os.path.exists("/etc/arch-release")
    
    # Required system libraries for Flet/Flutter rendering on Linux
    deps = ["libgtk-3-dev", "libgst-full-1.0"] if not is_arch else ["gtk3", "gst-plugins-good"]
    
    if is_arch:
        print("💡 ARCH USER DETECTED. If the app fails to open, run:")
        print("   sudo pacman -S gtk3 gst-plugins-good python-pip")
    else:
        print("💡 DEBIAN/UBUNTU USER DETECTED. Run if needed:")
        print("   sudo apt install libgtk-3-0 libgst-full-1.0")

def setup_python_deps():
    """Ensures all required Python libraries are installed."""
    print("🔍 Validating Python libraries...")
    required = ["flet", "requests", "packaging"]
    
    try:
        # Use the current python executable to install
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + required)
        print("✅ Python libraries ready.")
    except Exception as e:
        print(f"❌ Failed to install libraries: {e}")

def run_mobile_test():
    """Ensures paths are correct and launches the mobile app."""
    # Add root to PYTHONPATH so 'core' is found correctly
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

    print(f"🚀 Launching Mobile App from {mobile_script}...")
    try:
        # Launching with the modified environment to ensure 'core' is visible
        subprocess.run([sys.executable, mobile_script], env=env)
    except KeyboardInterrupt:
        print("\n🛑 App closed.")

if __name__ == "__main__":
    print("=== FOCUS STATION MOBILE SETUP & TEST ===")
    check_system_deps()
    setup_python_deps()
    run_mobile_test()