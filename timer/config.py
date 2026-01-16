# config.py
import customtkinter as ctk

# Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Constants
FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"
CONFIG_FILE = "user_config.json"
TASKS_FILE = "user_tasks.json"

# Wheel Colors
WHEEL_COLORS = ["#EF5350", "#AB47BC", "#5C6BC0", "#29B6F6", "#26A69A", "#9CCC65", "#FFA726", "#FF7043"]