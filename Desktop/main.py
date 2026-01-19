import sys
import os
import time
import logging
import traceback
import tkinter.messagebox as msgbox

# ---------------------------------------------------------
# 1. CRITICAL: CALCULATE PATHS FIRST
# ---------------------------------------------------------
try:
    if getattr(sys, 'frozen', False):
        # If run as .exe, use the executable's folder
        app_dir = os.path.dirname(sys.executable)
    else:
        # If run as script, use the script's folder
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # Force the app to work from this directory
    os.chdir(app_dir)

except Exception as e:
    # If this fails, we are in big trouble, but try to continue
    app_dir = os.getcwd()

# ---------------------------------------------------------
# 2. SETUP LOGGING (Safe Location)
# ---------------------------------------------------------
# We write the log next to the app so we know the folder exists
log_path = os.path.join(app_dir, "debug_run.txt")

logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

logging.info("--------------------------------------------------")
logging.info(" APP STARTUP - DEBUG MODE (FIXED)")
logging.info("--------------------------------------------------")
logging.info(f"App Directory: {app_dir}")
logging.info(f"Log File Path: {log_path}")

# List files to verify we see user_config.json
try:
    files = os.listdir(app_dir)
    logging.info(f"Files in directory: {files}")
    if "user_config.json" in files:
        logging.info("✅ user_config.json FOUND.")
    else:
        logging.error("❌ user_config.json NOT FOUND.")
except Exception as e:
    logging.error(f"Could not list files: {e}")

# ---------------------------------------------------------
# 3. IMPORTS
# ---------------------------------------------------------
# Fix console crash
if sys.stderr is None: sys.stderr = open(os.devnull, "w")
if sys.stdout is None: sys.stdout = open(os.devnull, "w")

import unicodedata
import idna
import customtkinter as ctk
import json
import config
from view_tasks import TaskManager
from view_ui import MainUI
from updater import AppUpdater
from core.task_manager import TaskManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Focus Station v{config.CURRENT_VERSION}") 
        self.geometry("1100x700")
        
        # Icon Loader
        try: 
            if os.path.exists("icon.ico"):
                self.iconbitmap("icon.ico")
        except Exception as e: 
            logging.error(f"Icon error: {e}")

        self.username = "Guest"
        self.updater = AppUpdater(self.on_update_found)
        self.updater.check_for_updates()
        self.task_manager = TaskManager(self)
        
        # Load User Logic
        if self.load_user_safe():
            logging.info(f"User loaded successfully: {self.username}")
            self.launch_main_ui()
        else:
            logging.info("User load failed or file missing. Showing Login.")
            self.show_login()

    def load_user_safe(self):
        try:
            if os.path.exists(config.CONFIG_FILE):
                with open(config.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", "Guest")
                    return True
        except Exception as e:
            logging.error(f"Error reading user config: {e}")
        return False

    def save_user_locally(self):
        logging.info(f"Saving user to: {os.path.abspath(config.CONFIG_FILE)}")
        try:
            with open(config.CONFIG_FILE, "w") as f:
                json.dump({"username": self.username}, f)
            logging.info("Save successful.")
            return True
        except Exception as e:
            logging.error(f"Save failed: {e}")
            logging.error(traceback.format_exc())
            # SHOW POPUP ON ERROR
            msgbox.showerror("Save Error", f"Could not save config file!\n\nError: {e}\n\nPath: {os.getcwd()}")
            return False

    # --- UPDATER ---
    def on_update_found(self, found, version_str):
        if found:
            self.new_version_str = version_str
            self.after(0, self.show_update_banner)

    def show_update_banner(self):
        self.update_frame = ctk.CTkFrame(self, fg_color="#10b981", height=40, corner_radius=0)
        self.update_frame.place(relx=0, rely=0, relwidth=1)
        ctk.CTkLabel(self.update_frame, text=f"NEW VERSION ({self.new_version_str})", font=("Roboto", 12, "bold"), text_color="white").pack(side="left", padx=20)
        ctk.CTkButton(self.update_frame, text="UPDATE NOW", width=100, height=25, fg_color="white", text_color="#10b981", command=self.start_update).pack(side="right", padx=20)

    def start_update(self):
        for w in self.update_frame.winfo_children(): w.destroy()
        self.progress_bar = ctk.CTkProgressBar(self.update_frame, width=300, progress_color="white")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.updater.perform_update(self.update_progress)

    def update_progress(self, percent):
        if percent == -1: return
        self.after(0, lambda: self.progress_bar.set(percent))

    # --- LOGIN ---
    def show_login(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Roboto", 26, "bold")).pack(pady=30)
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter username...", width=300, height=50, font=("Arial", 14))
        self.username_entry.pack(pady=10)
        ctk.CTkButton(self.login_frame, text="ENTER STATION", width=300, height=50, font=("Arial", 14, "bold"), fg_color="#1E88E5", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        logging.info("Login Button Clicked.")
        try:
            name = self.username_entry.get()
            if name.strip():
                self.username = name
                # Try save
                self.save_user_locally()
                self.login_frame.destroy()
                self.launch_main_ui()
            else:
                logging.warning("Empty username entered.")
        except Exception as e:
            logging.critical(f"LOGIN CRASH: {e}")
            msgbox.showerror("Login Crash", f"Error: {e}")

    def launch_main_ui(self):
        self.ui = MainUI(self, self, self.username, self.task_manager)
        self.ui.pack(fill="both", expand=True)
        if hasattr(self, 'update_frame'): self.update_frame.lift()

if __name__ == "__main__":
    try:
        app = FocusApp()
        app.mainloop()
    except Exception as e:
        logging.critical(f"MAINLOOP CRASH: {e}")
        logging.critical(traceback.format_exc())