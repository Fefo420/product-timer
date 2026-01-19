# core/config.py

# 🟢 REMOVED: import customtkinter as ctk 
# (This prevents mobile crashes!)

def apply_desktop_theme():
    """Only called by the Desktop app to avoid mobile crashes."""
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("Dark")
    except ImportError:
        pass

# Constants (Shared by Desktop and Mobile)
GITHUB_USER = "fefo420"
GITHUB_REPO = "product-timer"
CURRENT_VERSION = "0.9.0"

VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/timer/version.txt"
RELEASE_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest/download/"
FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"
CONFIG_FILE = "user_config.json"
TASKS_FILE = "user_tasks.json"