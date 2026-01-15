import os
import sys
import subprocess
import platform
import shutil
import venv

# Name of the internal sandbox folder
VENV_NAME = "build_env"

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
    required = ['customtkinter', 'requests', 'plyer', 'pyinstaller']
    pip_exe = get_venv_pip()
    
    print("🔍 Checking and installing dependencies inside sandbox...")
    # We use the venv's pip to install safely
    subprocess.check_call([pip_exe, "install"] + required)

def build_executable():
    """Runs PyInstaller using the VIRTUAL environment's Python"""
    os_name = platform.system()
    print(f"💻 Detected System: {os_name}")
    
    # Smart Path Detection
    if os.path.exists("timer.py"):
        script_path = "timer.py"
    elif os.path.exists(os.path.join("timer", "timer.py")):
        script_path = os.path.join("timer", "timer.py")
    else:
        print("❌ ERROR: Could not find 'timer.py'.")
        return

    icon_path = "icon.ico"
    app_name = "FocusTimer"
    
    # We run PyInstaller using the SANDBOX Python, not the System Python
    venv_python = get_venv_python()
    
    # Base command
    cmd = [
        venv_python, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
        "--collect-all", "customtkinter",
    ]

    # OS Specific Settings
    if os.path.exists(icon_path):
        if os_name == "Windows":
            cmd.append(f"--icon={icon_path}")
            cmd.append(f"--add-data={icon_path};.") 
        elif os_name == "Darwin": # Mac
            # Mac doesn't strictly use .ico for the app icon (needs .icns), 
            # but we include it for internal use
            cmd.append(f"--add-data={icon_path}:.")
        elif os_name == "Linux":
            cmd.append(f"--add-data={icon_path}:.")
    
    cmd.append(script_path)

    print("🚀 Starting Build Process... (This may take a minute)")
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*30)
        print("✅ BUILD COMPLETE!")
        print(f"Go to the 'dist' folder to find your {app_name} app.")
        print("="*30)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")

if __name__ == "__main__":
    try:
        # 1. Create the sandbox
        setup_virtual_env()
        # 2. Install libraries INTO the sandbox
        install_dependencies()
        # 3. Build using the sandbox tools
        build_executable()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("Press Enter to exit...")