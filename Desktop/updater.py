import requests
import os
import sys
import platform
import subprocess
import time
import threading
import logging
from packaging import version
import config

# --- DEBUG SETUP ---
# Log to a file next to the executable
if getattr(sys, 'frozen', False):
    log_path = os.path.join(os.path.dirname(sys.executable), "debug_updater.log")
else:
    log_path = "debug_updater.log"

logging.basicConfig(
    filename=log_path, 
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w' # Overwrite log each time
)

class AppUpdater:
    def __init__(self, ui_callback=None):
        self.ui_callback = ui_callback 
        self.os_type = platform.system()
        self.exe_name = "FocusTimer.exe" if self.os_type == "Windows" else "FocusTimer"
        logging.info(f"Updater initialized. OS: {self.os_type}")

    def check_for_updates(self):
        threading.Thread(target=self._worker_check, daemon=True).start()

    def _worker_check(self):
        try:
            logging.info(f"Checking updates at: {config.VERSION_URL}")
            r = requests.get(config.VERSION_URL, timeout=5)
            
            if r.status_code != 200:
                logging.error(f"Server error: {r.status_code}")
                return

            remote_ver_str = r.text.strip()
            remote_ver = version.parse(remote_ver_str)
            current_ver = version.parse(config.CURRENT_VERSION)

            logging.info(f"Current: {current_ver}, Remote: {remote_ver}")

            if remote_ver > current_ver:
                if self.ui_callback: self.ui_callback(True, remote_ver_str)
            else:
                if self.ui_callback: self.ui_callback(False, None)
                    
        except Exception as e:
            logging.error(f"Check Failed: {e}")

    def perform_update(self, progress_callback=None):
        threading.Thread(target=self._worker_update, args=(progress_callback,), daemon=True).start()

    def _worker_update(self, progress_callback):
        try:
            download_url = f"{config.RELEASE_URL}{self.exe_name}"
            logging.info(f"Downloading from: {download_url}")

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
                            progress_callback(downloaded / total_size)

            logging.info("Download complete.")
            self._restart_and_replace(new_file_path)

        except Exception as e:
            logging.error(f"Update Failed: {e}")
            if progress_callback: progress_callback(-1)

    def _restart_and_replace(self, new_file_path):
        current_exe = sys.executable
        logging.info("Starting restart sequence...")
        
        if not getattr(sys, 'frozen', False):
            print("Running in dev mode. Skipping restart logic.")
            return

        exe_dir = os.path.dirname(current_exe)
        bat_path = os.path.join(exe_dir, "update_installer.bat")
        old_file_path = current_exe + ".old"

        try:
            if os.path.exists(old_file_path):
                try: os.remove(old_file_path)
                except: pass

            os.rename(current_exe, old_file_path)
            os.rename(new_file_path, current_exe)
            logging.info("Files renamed successfully.")
            
            # ⚡ SPEED UPDATE: Changed timeout from 5 to 1
            bat_content = f"""
@echo off
timeout /t 2 /nobreak > nul
del "{old_file_path}"
explorer.exe "{current_exe}"
del "%~f0"
"""
            with open(bat_path, "w") as f:
                f.write(bat_content)
            logging.info("Batch file created.")

            logging.info("Launching batch file...")
            
            if self.os_type == "Windows":
                subprocess.Popen([bat_path], shell=True, cwd=exe_dir)
            else:
                env = os.environ.copy()
                if "_MEIPASS2" in env: del env["_MEIPASS2"]
                subprocess.Popen([current_exe], env=env)
                
            logging.info("Exiting Python process now.")
            os._exit(0) 

        except Exception as e:
            logging.error(f"Swap Failed: {e}")
            if os.path.exists(old_file_path) and not os.path.exists(current_exe):
                os.rename(old_file_path, current_exe)