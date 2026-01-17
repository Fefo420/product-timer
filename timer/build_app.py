import os
import sys
import subprocess
import platform
import shutil
import venv

# Name of the internal sandbox folder
VENV_NAME = "build_env"

def check_system_deps():
    """
    Checks for system-level dependencies (Tkinter, Venv) and attempts to install them
    automatically on Linux if they are missing.
    """
    if platform.system() == "Linux":
        print("🐧 Linux detected. Checking system components...")
        
        # 1. Check for Tkinter (GUI Support)
        try:
            import tkinter
            print("✅ Tkinter is installed.")
        except ImportError:
            print("⚠️ Tkinter missing. Attempting to install...")
            install_linux_package("python3-tk")

        # 2. Check for Ensurepip/Venv (Virtual Environment Support)
        try:
            import ensurepip
            import venv
            # Just importing isn't enough, sometimes the module exists but is broken
            # without the system package (common in Ubuntu/Debian).
            print("✅ Venv/Ensurepip is installed.")
        except ImportError:
            print("⚠️ Venv module missing. Attempting to install...")
            # Detect python version (e.g., "python3.12")
            py_version = f"python{sys.version_info.major}.{sys.version_info.minor}-venv"
            install_linux_package(py_version)

def install_linux_package(package_name):
    """Helper to run apt-get commands safely"""
    if not shutil.which("apt-get"):
        print(f"❌ Could not install {package_name}: 'apt-get' not found.")
        sys.exit(1)

    # Check if we are root (don't use sudo if we are already root)
    use_sudo = os.geteuid() != 0
    cmd_prefix = ['sudo'] if use_sudo else []

    try:
        print(f"📦 Installing {package_name}...")
        subprocess.check_call(cmd_prefix + ['apt-get', 'update'])
        subprocess.check_call(cmd_prefix + ['apt-get', 'install', '-y', package_name])
        print(f"✅ Installed {package_name} successfully.")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}. Please install it manually.")
        sys.exit(1)

def get_venv_python():
    if platform.system() == "Windows":
        return os.path.abspath(os.path.join(VENV_NAME, "Scripts", "python.exe"))
    else:
        return os.path.abspath(os.path.join(VENV_NAME, "bin", "python"))

def get_venv_pip():
    if platform.system() == "Windows":
        return os.path.abspath(os.path.join(VENV_NAME, "Scripts", "pip.exe"))
    else:
        return os.path.abspath(os.path.join(VENV_NAME, "bin", "pip"))

def setup_virtual_env():
    # Detect if we need to recreate the environment
    if os.path.exists(VENV_NAME):
        # Optional: Check if the existing venv is broken
        if not os.path.exists(get_venv_python()):
            print("⚠️ Existing venv seems broken. Recreating...")
            shutil.rmtree(VENV_NAME)
    
    if not os.path.exists(VENV_NAME):
        print(f"📦 Creating isolated environment '{VENV_NAME}'...")
        try:
            venv.create(VENV_NAME, with_pip=True)
        except Exception as e:
            print(f"❌ Failed to create venv: {e}")
            print("💡 Try running: sudo apt install python3-venv")
            sys.exit(1)

def install_dependencies():
    # Force reinstall to ensure fresh files
    required = ['customtkinter', 'requests', 'plyer', 'pyinstaller', 'packaging', 'pillow']
    pip_exe = get_venv_pip()
    print("🔍 Checking and installing Python libraries...")
    subprocess.check_call([pip_exe, "install", "--upgrade", "--force-reinstall"] + required)

def build_executable():
    os_name = platform.system()
    print(f"💻 Detected System: {os_name}")
    
    if os.path.exists("main.py"):
        script_path = os.path.abspath("main.py")
    elif os.path.exists(os.path.join("timer", "timer.py")):
        script_path = os.path.abspath(os.path.join("timer", "timer.py"))
    else:
        print("❌ ERROR: Could not find 'main.py'.")
        return

    icon_path = os.path.abspath("icon.ico")
    app_name = "FocusTimer"
    
    venv_python = get_venv_python()
    
    # Base command
    cmd = [
        venv_python, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
        "--clean",
        "--windowed",
        "--collect-all", "customtkinter",
        "--hidden-import", "unicodedata",
        "--hidden-import", "idna",
    ]

    separator = ";" if os_name == "Windows" else ":"

    if os.path.exists(icon_path):
        cmd.append(f"--add-data={icon_path}{separator}.")
        if os_name == "Windows":
            cmd.append(f"--icon={icon_path}")

    cmd.append(script_path)

    print("🚀 Starting Build Process...")
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*30)
        print("✅ BUILD COMPLETE!")
        print(f"Go to the 'dist' folder to find your {app_name} file.")
        print("="*30)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")

if __name__ == "__main__":
    try:
        # CLEAN SLATE: Nuke everything to prevent "Zombie" builds
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        if os.path.exists("FocusTimer.spec"): os.remove("FocusTimer.spec")
        
        # 🟢 Run the new robust checks
        check_system_deps()
        
        setup_virtual_env()
        install_dependencies()
        build_executable()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if platform.system() == "Windows":
        input("Press Enter to exit...")