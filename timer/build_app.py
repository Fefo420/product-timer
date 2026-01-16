import os
import sys
import subprocess
import platform
import shutil
import venv

# Name of the internal sandbox folder
VENV_NAME = "build_env"

def check_system_deps():
    if platform.system() == "Linux":
        print("🐧 Linux detected. Checking system components...")
        try:
            import tkinter
            print("✅ Tkinter is already installed.")
        except ImportError:
            if shutil.which("apt-get"):
                try:
                    subprocess.check_call(['sudo', 'apt-get', 'update'])
                    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'python3-tk'])
                except subprocess.CalledProcessError:
                    sys.exit(1)
            else:
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
    if not os.path.exists(VENV_NAME):
        print(f"📦 Creating isolated environment '{VENV_NAME}'...")
        venv.create(VENV_NAME, with_pip=True)

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
        # 🟢 FIX 1: Automatically find ALL customtkinter files (themes/fonts/json)
        "--collect-all", "customtkinter",
        # 🟢 FIX 2: Force include the missing text libraries
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
        # 🟢 CLEAN SLATE: Nuke everything to prevent "Zombie" builds
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        if os.path.exists("FocusTimer.spec"): os.remove("FocusTimer.spec")
        
        check_system_deps()
        setup_virtual_env()
        install_dependencies()
        build_executable()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if platform.system() == "Windows":
        input("Press Enter to exit...")