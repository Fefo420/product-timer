import flet as ft
from datetime import datetime
import sys
import os
import threading
import time

# Ensure the root directory is accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.data_manager import TaskManager 

def main(page: ft.Page):
    # 📱 Responsive Window Settings
    page.window.width = 380
    page.window.height = 720
    page.window.resizable = False
    page.title = "Focus Station"
    page.bgcolor = "#0f172a" # Matches BG_COLOR
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    
    manager = TaskManager(username="MobileUser")

    # --- TIMER LOGIC ---
    timer_data = {"running": False, "seconds": 1500}

    def format_time(s):
        mins, secs = divmod(s, 60)
        return f"{mins:02d}:{secs:02d}"

    def update_timer():
        while timer_data["running"] and timer_data["seconds"] > 0:
            time.sleep(1)
            timer_data["seconds"] -= 1
            timer_text.value = format_time(timer_data["seconds"])
            progress_ring.value = timer_data["seconds"] / 1500
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
    timer_text = ft.Text(format_time(timer_data["seconds"]), size=36, weight="bold")
    
    progress_ring = ft.ProgressRing(
        value=1.0, stroke_width=6, width=130, height=130, color="#6366f1" # ACCENT_COLOR
    )

    start_btn = ft.FilledButton(
        content=ft.Text("START SESSION", weight="bold"), 
        on_click=toggle_timer,
        style=ft.ButtonStyle(bgcolor="#6366f1", color="white"),
        width=220
    )

    task_input = ft.TextField(
        label="New goal...", 
        expand=True, 
        height=48, 
        text_size=14,
        bgcolor="#1e293b", # CARD_COLOR
        border_radius=10,
        on_submit=lambda _: refresh_tasks()
    )
    
    tasks_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=5)

    def refresh_tasks(e=None):
        tasks_column.controls.clear()
        date_key = manager.get_key(datetime.now())
        tasks = manager.load_data().get(date_key, [])
        for t in tasks:
            if not t.get("done", False):
                tasks_column.controls.append(
                    ft.Checkbox(label=t["text"], label_style=ft.TextStyle(size=14))
                )
        page.update()

    # --- LAYOUT ASSEMBLY ---
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("FOCUS STATION", size=18, weight="bold", color="#6366f1"),
                ft.Stack([
                    progress_ring,
                    # 🟢 FIXED: Using string "center" instead of ft.alignment.center
                    ft.Container(content=timer_text, alignment="center", width=130, height=130)
                ], alignment="center"),
                start_btn,
                ft.Divider(height=20, color="#334155"),
                ft.Row([
                    task_input, 
                    ft.IconButton(icon="add", icon_color="#6366f1", on_click=refresh_tasks)
                ]),
                ft.Text("TODAY'S TASKS", size=11, color="#94a3b8", weight="bold"),
                ft.Container(
                    content=tasks_column,
                    expand=True,
                    bgcolor="#020617", # SIDEBAR_COLOR
                    padding=10,
                    border_radius=12
                )
            ], horizontal_alignment="center", spacing=15),
            expand=True
        )
    )
    
    refresh_tasks()

if __name__ == "__main__":
    # 🟢 FIXED: Modern syntax to avoid DeprecationWarning
    ft.app(main)