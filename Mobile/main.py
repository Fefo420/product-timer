import flet as ft
from datetime import datetime
import sys
import os
import platform

# 1. CROSS-PLATFORM PATH FIX
# This ensures 'core' is found whether you are on Windows or Linux
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from core.data_manager import TaskManager
    print("--- DEBUG: TaskManager imported ---")
except Exception as e:
    print(f"--- DEBUG ERROR: Import failed: {e} ---")

def main(page: ft.Page):
    # 2. LINUX COMPATIBILITY SETTINGS
    # Some Linux environments (like WSL) don't support fixed window sizes well
    if platform.system() != "Linux":
        page.window_width = 380
        page.window_height = 700
        page.window_resizable = False
    
    page.title = "Focus Station"
    page.bgcolor = "#0f172a" # BG_COLOR from desktop
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    manager = TaskManager(username="MobileUser")

    # 3. UI COMPONENTS (Modern Flet Syntax)
    task_input = ft.TextField(
        label="What's the plan?",
        bgcolor="#1e293b", # CARD_COLOR from desktop
        color="white",
        border_radius=12,
        expand=True
    )

    tasks_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def add_task(e):
        if not task_input.value: return
        try:
            date_key = manager.get_key(datetime.now())
            data = manager.load_data()
            tasks = data.get(date_key, [])
            tasks.append({"text": task_input.value, "done": False})
            data[date_key] = tasks
            manager.save_data(data)
            task_input.value = ""
            refresh_tasks()
        except Exception as ex:
            print(f"Error saving task: {ex}")

    def refresh_tasks():
        tasks_column.controls.clear()
        date_key = manager.get_key(datetime.now())
        tasks = manager.load_data().get(date_key, [])
        for t in tasks:
            if not t.get("done", False):
                tasks_column.controls.append(
                    ft.Checkbox(label=t["text"], value=False)
                )
        page.update()

    # Layout matches the indigo/slate theme
    page.add(
        ft.Text("FOCUS STATION", size=22, weight="bold"),
        ft.Row([
            task_input, 
            ft.IconButton(icon="add", icon_color="#6366f1", on_click=add_task)
        ]),
        ft.Divider(color="#334155"),
        tasks_column
    )
    refresh_tasks()

# 4. UNIVERSAL LAUNCHER
# On Linux/WSL, if a window fails to open, this will automatically
# fallback to a web-based view so you can still test it.
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        print("💡 Desktop window not supported. Launching in Web View...")
        ft.app(target=main, view=ft.AppView.WEB_BROWSER)