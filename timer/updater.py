import requests
import os
import sys
import platform
import subprocess
import time
import threading
from packaging import version
import config

class AppUpdater:
    def __init__(self, ui_callback=None):
        self.ui_callback = ui_callback # Function to call to update UI status
        self.os_type = platform.system()
        self.exe_name = "FocusTimer.exe" if self.os_type == "Windows" else "FocusTimer"

    def check_for_updates(self):
        """Runs in background to check version"""
        threading.Thread(target=self._worker_check, daemon=True).start()

    def _worker_check(self):
        try:
            print(f"Checking updates at: {config.VERSION_URL}")
            r = requests.get(config.VERSION_URL, timeout=5)
            
            # 🟢 CHANGE THIS PART:
            if r.status_code != 200:
                print(f"❌ Error! Server returned code: {r.status_code}") # Print the error!
                return

            remote_ver_str = r.text.strip()
            remote_ver = version.parse(remote_ver_str)
            current_ver = version.parse(config.CURRENT_VERSION)

            print(f"Current: {current_ver}, Remote: {remote_ver}")

            # 2. Compare
            if remote_ver > current_ver:
                if self.ui_callback:
                    self.ui_callback(True, remote_ver_str)
            else:
                if self.ui_callback:
                    self.ui_callback(False, None)
                    
        except Exception as e:
            print(f"Update Check Failed: {e}")

    def perform_update(self, progress_callback=None):
        """Downloads and installs the update"""
        threading.Thread(target=self._worker_update, args=(progress_callback,), daemon=True).start()

    def _worker_update(self, progress_callback):
        try:
            # 1. Determine Download URL
            download_url = f"{config.RELEASE_URL}{self.exe_name}"
            print(f"Downloading from: {download_url}")

            # 2. Download File
            r = requests.get(download_url, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            # Save as .new temporary file
            new_file_path = os.path.join(os.path.dirname(sys.executable), self.exe_name + ".new")
            
            with open(new_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            percent = downloaded / total_size
                            progress_callback(percent)

            print("Download complete.")
            
            # 3. The Swap Magic
            self._restart_and_replace(new_file_path)

        except Exception as e:
            print(f"Update Failed: {e}")
            if progress_callback: progress_callback(-1) # Error

    def _restart_and_replace(self, new_file_path):
        """
        Rename current -> .old
        Rename .new -> current
        Restart
        """
        current_exe = sys.executable
        
        # If we are running from a script (development mode), don't delete main.py!
        if not getattr(sys, 'frozen', False):
            print("Running in dev mode (not frozen). Skipping restart logic.")
            return

        old_file_path = current_exe + ".old"

        try:
            # Windows allows renaming a running executable!
            if os.path.exists(old_file_path):
                os.remove(old_file_path) # Clean up previous update mess if any

            os.rename(current_exe, old_file_path)
            os.rename(new_file_path, current_exe)
            
            # Make sure it's executable (Linux/Mac)
            if self.os_type != "Windows":
                os.chmod(current_exe, 0o755)

            # 4. Relaunch
            print("Relaunching...")
            
            # Use this to hide the black console window on restart
            if self.os_type == "Windows":
                subprocess.Popen([current_exe], creationflags=0x08000000)
            else:
                subprocess.Popen([current_exe])
                
            # 🔴 THE FIX: Use os._exit(0) instead of sys.exit(0)
            # sys.exit() only kills the thread. os._exit(0) kills the whole app.
            os._exit(0) 

        except Exception as e:
            print(f"Swap Failed: {e}")
            # Try to rollback
            if os.path.exists(old_file_path) and not os.path.exists(current_exe):
                os.rename(old_file_path, current_exe)