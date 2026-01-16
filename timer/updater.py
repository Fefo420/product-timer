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
        self.ui_callback = ui_callback 
        self.os_type = platform.system()
        self.exe_name = "FocusTimer.exe" if self.os_type == "Windows" else "FocusTimer"

    def check_for_updates(self):
        """Runs in background to check version"""
        threading.Thread(target=self._worker_check, daemon=True).start()

    def _worker_check(self):
        try:
            print(f"Checking updates at: {config.VERSION_URL}")
            r = requests.get(config.VERSION_URL, timeout=5)
            
            if r.status_code != 200:
                print(f"❌ Error! Server returned code: {r.status_code}")
                return

            remote_ver_str = r.text.strip()
            remote_ver = version.parse(remote_ver_str)
            current_ver = version.parse(config.CURRENT_VERSION)

            print(f"Current: {current_ver}, Remote: {remote_ver}")

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
            download_url = f"{config.RELEASE_URL}{self.exe_name}"
            print(f"Downloading from: {download_url}")

            r = requests.get(download_url, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
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
            self._restart_and_replace(new_file_path)

        except Exception as e:
            print(f"Update Failed: {e}")
            if progress_callback: progress_callback(-1)

    def _restart_and_replace(self, new_file_path):
        current_exe = sys.executable
        
        if not getattr(sys, 'frozen', False):
            print("Running in dev mode. Skipping restart logic.")
            return

        old_file_path = current_exe + ".old"

        try:
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

            os.rename(current_exe, old_file_path)
            os.rename(new_file_path, current_exe)
            
            if self.os_type != "Windows":
                os.chmod(current_exe, 0o755)

            print("Relaunching...")
            
            # 🟢 THE FIX: Clean the environment to prevent "Poisoning"
            # We must remove _MEIPASS2 so the child process creates its OWN temp folder.
            env = os.environ.copy()
            if "_MEIPASS2" in env:
                del env["_MEIPASS2"]

            if self.os_type == "Windows":
                subprocess.Popen(
                    [current_exe], 
                    creationflags=0x08000000, 
                    cwd=os.path.dirname(current_exe), # Ensure correct working dir
                    env=env # Pass the clean environment
                )
            else:
                subprocess.Popen(
                    [current_exe], 
                    cwd=os.path.dirname(current_exe),
                    env=env
                )
                
            os._exit(0) 

        except Exception as e:
            print(f"Swap Failed: {e}")
            if os.path.exists(old_file_path) and not os.path.exists(current_exe):
                os.rename(old_file_path, current_exe)