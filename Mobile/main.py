import os
import sys
import time
import threading
from datetime import datetime
import flet as ft

# 🟢 RENDER FIX: Force software rendering for Windows to avoid the grey box
if sys.platform == "win32":
    os.environ["FLET_RENDERER_TYPE"] = "software"

# Path setup to find the shared 'core' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.data_manager import TaskManager 

def main(page: ft.Page):
    # 📱 Window Configuration
    page.title = "Focus Station"
    page.window.width = 380
    page.window.height = 720
    page.bgcolor = "#0f172a"  # Matches desktop BG_COLOR
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # Initialize the shared data manager
    manager = TaskManager(username="MobileUser")
    timer_data = {"running": False, "seconds": 1500}

    # --- TIMER LOGIC ---
    def format_time(s):
        mins, secs = divmod(s, 60)
        return f"{mins:02d}:{secs:02d}"

    def update_timer():
        while timer_data["running"] and timer_data["seconds"] > 0:
            time.sleep(1)
            timer_data["seconds"] -= 1
            timer_text.value = format_time(timer_data["seconds"])
            page.update()
        
        if timer_data["seconds"] == 0:
            timer_data["running"] = False
            start_btn.content.value = "START SESSION"
            page.update()

    def toggle_timer(e):
        if not timer_data["running"]:
            timer_data["running"] = True
            start_btn.content.value = "PAUSE"
            threading.Thread(target=update_timer, daemon=True).start()
        else:
            timer_data["running"] = False
            start_btn.content.value = "RESUME"
        page.update()

    # --- UI COMPONENTS ---
    # Using white for high visibility on the dark background
    timer_text = ft.Text("25:00", size=48, weight="bold", color="white")
    
    # Standard button for session control
    start_btn = ft.FilledButton(
        content=ft.Text("START SESSION", weight="bold"),
        on_click=toggle_timer,
        style=ft.ButtonStyle(bgcolor="#6366f1", color="white"),
        width=250
    )

    task_input = ft.TextField(
        label="Add a task...", 
        bgcolor="#1e293b", # Matches desktop CARD_COLOR
        expand=True,
        on_submit=lambda _: add_task()
    )
    
    tasks_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def add_task():
        if not task_input.value: return
        # Save task using shared logic from core
        date_key = manager.get_key(datetime.now())
        data = manager.load_data()
        tasks = data.get(date_key, [])
        tasks.append({"text": task_input.value, "done": False})
        data[date_key] = tasks
        manager.save_data(data)
        
        task_input.value = ""
        refresh_tasks()

    def refresh_tasks():
        tasks_list.controls.clear()
        # Load tasks from the shared JSON file
        data = manager.load_data()
        date_key = manager.get_key(datetime.now())
        tasks = data.get(date_key, [])
        for t in tasks:
            if not t.get("done", False):
                tasks_list.controls.append(ft.Checkbox(label=t["text"]))
        page.update()

    # --- LAYOUT ---
    page.add(
        ft.Text("FOCUS STATION", size=20, weight="bold", color="#6366f1"),
        ft.Divider(height=20, color="transparent"),
        # 🟢 FIXED: Using string "center" to avoid alignment errors
        ft.Container(content=timer_text, alignment=ft.alignment.Alignment(0, 0)),
        ft.Row([start_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(height=20),
        ft.Row([task_input, ft.IconButton(icon="add", on_click=lambda _: add_task())]),
        ft.Text("TODAY'S GOALS", size=12, color="gray", weight="bold"),
        tasks_list
    )

    # Initial load of tasks
    refresh_tasks()

if __name__ == "__main__":
    # 🟢 FIXED: Using target=main to match the latest Flet expectations
    ft.app(target=main)