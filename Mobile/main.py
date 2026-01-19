import flet as ft
from datetime import datetime
import sys
import os

# Add the parent directory to sys.path so we can find 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_manager import TaskManager

def main(page: ft.Page):
    # 1. Setup Page Theme
    page.title = "Focus Station Mobile"
    page.bgcolor = "#0f172a"  # Dark Slate
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    # Initialize Logic with a default user (Mobile needs a login screen later!)
    manager = TaskManager(username="MobileUser")

    # 2. UI Elements
    task_input = ft.TextField(
        hint_text="What needs to be done?",
        bgcolor="#1e293b",
        border_color="transparent",
        color="white",
        expand=True
    )

    tasks_column = ft.Column(scroll=ft.ScrollMode.AUTO)

    def add_task(e):
        if not task_input.value: return
        
        # Save to JSON using Shared Logic
        date_key = manager.get_key(datetime.now())
        data = manager.load_data()
        tasks = data.get(date_key, [])
        tasks.append({"text": task_input.value, "done": False})
        data[date_key] = tasks
        manager.save_data(data)
        
        # Clear and Refresh
        task_input.value = ""
        refresh_tasks()
        page.update()

    def mark_complete(task_text, checkbox):
        # Use Shared Logic
        manager.mark_done(task_text)
        checkbox.disabled = True
        page.update()

    def refresh_tasks():
        tasks_column.controls.clear()
        date_key = manager.get_key(datetime.now())
        tasks = manager.load_data().get(date_key, [])
        
        for t in tasks:
            if not t.get("done", False):
                # Create a Flet Checkbox
                cb = ft.Checkbox(
                    label=t["text"], 
                    value=False,
                    on_change=lambda e, text=t["text"]: mark_complete(text, e.control)
                )
                tasks_column.controls.append(cb)
        page.update()

    # 3. Build Layout
    add_btn = ft.IconButton(
        icon=ft.icons.ADD_CIRCLE, 
        icon_color="#6366f1", 
        icon_size=40, 
        on_click=add_task
    )

    page.add(
        ft.Row(
            [
                ft.Text("FOCUS STATION", size=20, weight="bold", color="white"),
                ft.Container(expand=True), # Spacer
                ft.Icon(ft.icons.TIMER, color="#6366f1")
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        ft.Divider(color="transparent", height=20),
        ft.Row([task_input, add_btn]),
        ft.Divider(color="gray"),
        tasks_column
    )

    refresh_tasks()

ft.app(target=main)