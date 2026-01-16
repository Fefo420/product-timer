# config.py
import customtkinter as ctk

# Appearance
ctk.set_appearance_mode("Dark")
# 🔴 DELETE THIS LINE: ctk.set_default_color_theme("green") 
# (We already set the theme in main.py, so this is redundant and causes crashes)

# Constants
GITHUB_USER = "fefo420"
GITHUB_REPO = "product-timer"  # Your Repository Name
CURRENT_VERSION = "1.0.1"      # Update this number manually before every build!

# URLs (Don't change these, they are automatic)
# Checks this raw file for the version number "1.0.1" etc.
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/timer/version.txt"

# Where to find the executable downloads
RELEASE_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest/download/"

# Database
FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"
CONFIG_FILE = "user_config.json"
TASKS_FILE = "user_tasks.json"

# Wheel Colors
WHEEL_COLORS = ["#EF5350", "#AB47BC", "#5C6BC0", "#29B6F6", "#26A69A", "#9CCC65", "#FFA726", "#FF7043"]