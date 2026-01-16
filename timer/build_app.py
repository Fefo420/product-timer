import os
import sys
import subprocess
import platform
import shutil
import venv

# Name of the internal sandbox folder
VENV_NAME = "build_env"

def check_system_deps():
    """Checks for system-level dependencies (Linux specific)"""
    if platform.system() == "Linux":
        print("🐧 Linux detected. Checking system components...")
        try:
            import tkinter
            print("✅ Tkinter is already installed.")
        except ImportError:
            print("⚠️  Tkinter (GUI helper) is missing!")
            if shutil.which("apt-get"):
                print("📦 Attempting to install 'python3-tk' via apt-get...")
                print("🔑 You may be asked for your password (sudo).")
                try:
                    subprocess.check_call(['sudo', 'apt-get', 'update'])
                    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'python3-tk'])
                    print("✅ System dependencies installed!")
                except subprocess.CalledProcessError:
                    print("❌ Automatic install failed. Run: sudo apt-get install python3-tk")
                    sys.exit(1)
            else:
                print("❌ Please install 'python3-tk' using your package manager (dnf, pacman, etc).")
                sys.exit(1)

def get_venv_python():
    """Returns the path to the Python executable inside the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(VENV_NAME, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_NAME, "bin", "python")

def get_venv_pip():
    """Returns the path to pip inside the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(VENV_NAME, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_NAME, "bin", "pip")

def setup_virtual_env():
    """Creates a virtual environment if it doesn't exist"""
    if not os.path.exists(VENV_NAME):
        print(f"📦 Creating isolated environment '{VENV_NAME}'...")
        venv.create(VENV_NAME, with_pip=True)
    else:
        print(f"✅ Found existing environment '{VENV_NAME}'")

def install_dependencies():
    """Installs required libraries into the VIRTUAL environment"""
    required = ['customtkinter', 'requests', 'plyer', 'pyinstaller', 'packaging', 'pillow']
    pip_exe = get_venv_pip()
    
    print("🔍 Checking and installing Python libraries...")
    subprocess.check_call([pip_exe, "install"] + required)

def build_executable():
    """Runs PyInstaller using the VIRTUAL environment's Python"""
    os_name = platform.system()
    print(f"💻 Detected System: {os_name}")
    
    if os.path.exists("timer.py"):
        script_path = "timer.py"
    elif os.path.exists(os.path.join("timer", "timer.py")):
        script_path = os.path.join("timer", "timer.py")
    else:
        print("❌ ERROR: Could not find 'timer.py'.")
        return

    icon_path = "icon.ico"
    app_name = "FocusTimer"
    
    venv_python = get_venv_python()
    
    # Base command
    cmd = [
        venv_python, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
        "--collect-all", "customtkinter",
    ]

    # Universal Icon Handling
    if os.path.exists(icon_path):
        # Windows uses ';' separator. Mac and Linux use ':'
        separator = ";" if os_name == "Windows" else ":"
        
        # Add the icon file to the internal bundle
        cmd.append(f"--add-data={icon_path}{separator}.")
        
        # On Windows, we can also set the .exe file icon directly
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
        check_system_deps()
        setup_virtual_env()
        install_dependencies()
        build_executable()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if platform.system() == "Windows":
        input("Press Enter to exit...")