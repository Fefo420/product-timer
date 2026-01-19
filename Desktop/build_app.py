import os
import sys
import subprocess
import platform
import shutil
import venv

# Name of the internal sandbox folder
VENV_NAME = "build_env"

def get_venv_executable(name):
    """Returns the path to an executable inside the venv (cross-platform)."""
    if platform.system() == "Windows":
        return os.path.abspath(os.path.join(VENV_NAME, "Scripts", f"{name}.exe"))
    else:
        return os.path.abspath(os.path.join(VENV_NAME, "bin", name))

def check_system_deps():
    """
    On Linux, ensures that Tkinter (GUI) and Venv (Virtual Environment)
    are installed at the system level before proceeding.
    """
    if platform.system() != "Linux":
        return

    print("🐧 Linux detected. Checking system components...")
    
    # Define system packages we might need
    # We dynamically find the venv package for the current python version (e.g. python3.12-venv)
    py_version_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"
    venv_pkg = f"{py_version_tag}-venv"
    tk_pkg = "python3-tk"

    packages_to_install = []

    # 1. Check Tkinter
    try:
        import tkinter
    except ImportError:
        print(f"⚠️  Missing {tk_pkg}")
        packages_to_install.append(tk_pkg)

    # 2. Check Venv (Trickier, sometimes import works but module is broken)
    # We try to run the module to see if it actually works
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"⚠️  Missing {venv_pkg}")
        packages_to_install.append(venv_pkg)

    if packages_to_install:
        print(f"📦 Installing missing system packages: {', '.join(packages_to_install)}...")
        install_linux_packages(packages_to_install)
        print("✅ System dependencies installed.")

def install_linux_packages(packages):
    """Runs apt-get install, handling sudo automatically."""
    if not shutil.which("apt-get"):
        print("❌ Error: 'apt-get' not found. Cannot auto-install dependencies.")
        sys.exit(1)

    # Don't use sudo if we are already root (e.g. Docker)
    cmd = ["apt-get", "update"]
    install_cmd = ["apt-get", "install", "-y"] + packages
    
    if os.geteuid() != 0:
        cmd.insert(0, "sudo")
        install_cmd.insert(0, "sudo")

    try:
        subprocess.check_call(cmd)
        subprocess.check_call(install_cmd)
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please run manually:")
        print(f"sudo apt install {' '.join(packages)}")
        sys.exit(1)

def setup_virtual_env():
    """Creates the virtual environment. Self-heals if the folder is broken."""
    pip_path = get_venv_executable("pip")
    
    # 🩹 SELF-HEALING LOGIC
    # If folder exists but pip is missing, it's a 'Zombie' build. Kill it.
    if os.path.exists(VENV_NAME) and not os.path.exists(pip_path):
        print("🧹 Found broken build environment. cleaning up...")
        shutil.rmtree(VENV_NAME)

    if not os.path.exists(VENV_NAME):
        print(f"📦 Creating isolated environment '{VENV_NAME}'...")
        try:
            venv.create(VENV_NAME, with_pip=True)
        except Exception as e:
            print(f"❌ Failed to create venv: {e}")
            sys.exit(1)

def install_dependencies():
    """Installs Python libraries into the venv."""
    required = ['customtkinter', 'requests', 'plyer', 'pyinstaller', 'packaging', 'pillow']
    pip_exe = get_venv_executable("pip")
    
    print("🔍 Checking Python libraries...")
    try:
        # We use --no-warn-script-location to keep logs clean
        subprocess.check_call([pip_exe, "install"] + required, stdout=subprocess.DEVNULL)
        print("✅ Python libraries installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install libraries: {e}")
        sys.exit(1)

def build_executable():
    """Runs PyInstaller."""
    os_name = platform.system()
    app_name = "FocusTimer"
    
    # Find the script
    if os.path.exists("main.py"):
        script_path = os.path.abspath("main.py")
    elif os.path.exists(os.path.join("timer", "timer.py")):
        script_path = os.path.abspath(os.path.join("timer", "timer.py"))
    else:
        print("❌ ERROR: Could not find 'main.py'.")
        return

    icon_path = os.path.abspath("icon.ico")
    python_exe = get_venv_executable("python")
    
    # PyInstaller Command
    cmd = [
        python_exe, "-m", "PyInstaller",
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

    print("🚀 Starting Build Process... (This might take a minute)")
    try:
        # Run build
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL) # Hide spammy logs
        
        print("\n" + "="*40)
        print("✅ BUILD SUCCESSFUL!")
        output_file = os.path.join("dist", app_name + (".exe" if os_name == "Windows" else ""))
        print(f"📁 Output: {output_file}")
        print("="*40)
        
    except subprocess.CalledProcessError:
        print("\n❌ PyInstaller Failed. Removing 'build' and trying once more might fix cache issues.")

if __name__ == "__main__":
    try:
        # Clean previous build artifacts (standard cleanup)
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        if os.path.exists("FocusTimer.spec"): os.remove("FocusTimer.spec")
        
        check_system_deps()   # 1. Install Linux system packages (sudo apt ...)
        setup_virtual_env()   # 2. Create venv (and delete broken ones)
        install_dependencies()# 3. Pip install inside venv
        build_executable()    # 4. PyInstaller
        
    except KeyboardInterrupt:
        print("\n🛑 Build cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")