import os
import sys
import subprocess
import platform

def install_package(package):
    """Installs a package using pip"""
    print(f"📦 Installing missing package: {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_dependencies():
    """Checks and installs required libraries"""
    required = ['customtkinter', 'requests', 'plyer', 'pyinstaller']
    print("🔍 Checking dependencies...")
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            install_package(package)

def build_executable():
    """Runs PyInstaller with settings based on the User's OS"""
    os_name = platform.system()
    print(f"💻 Detected System: {os_name}")
    
    # --- SMART PATH DETECTION ---
    # Check if we are inside the timer folder or outside it
    if os.path.exists("timer.py"):
        script_path = "timer.py"
        print("📂 Found script in current folder.")
    elif os.path.exists(os.path.join("timer", "timer.py")):
        script_path = os.path.join("timer", "timer.py")
        print("📂 Found script in subfolder 'timer/'.")
    else:
        print("❌ ERROR: Could not find 'timer.py'. Make sure you are in the right folder!")
        return

    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        print(f"⚠️ Warning: Could not find '{icon_path}'. Building without icon.")
        icon_path = None
        
    app_name = "FocusTimer"
    
    # Base command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
        "--collect-all", "customtkinter",
    ]

    # OS Specific Settings
    if icon_path:
        if os_name == "Windows":
            cmd.append(f"--icon={icon_path}")
            cmd.append(f"--add-data={icon_path};.") 
        elif os_name == "Darwin": # Mac
            cmd.append(f"--icon={icon_path}")
            cmd.append(f"--add-data={icon_path}:.")
        elif os_name == "Linux":
            cmd.append(f"--add-data={icon_path}:.")

    # Add the script file last
    cmd.append(script_path)

    print("🚀 Starting Build Process... (This may take a minute)")
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*30)
        print("✅ BUILD COMPLETE!")
        print(f"Go to the 'dist' folder to find your {app_name} app.")
        print("="*30)
    except subprocess.CalledProcessError:
        print("\n❌ Build Failed. Read the error message above.")

if __name__ == "__main__":
    try:
        check_dependencies()
        build_executable()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")