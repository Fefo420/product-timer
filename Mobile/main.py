import flet as ft
from datetime import datetime
import sys
import os

print("--- DEBUG: Starting Script ---")

# Ensure core is visible
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.data_manager import TaskManager
    print("--- DEBUG: TaskManager imported successfully ---")
except Exception as e:
    print(f"--- DEBUG ERROR: Import failed: {e} ---")

def main(page: ft.Page):
    print("--- DEBUG: main() function started ---")
    
    # 1. Page Settings
    page.title = "Focus Station"
    page.bgcolor = "#0f172a"
    page.padding = 30
    
    print("--- DEBUG: Page settings applied ---")

    # Initialize Logic
    try:
        manager = TaskManager(username="MobileUser")
        print("--- DEBUG: TaskManager instance created ---")
    except Exception as e:
        print(f"--- DEBUG ERROR: manager creation failed: {e} ---")

    # 2. UI Components (Using NEW Flet syntax)
    title_text = ft.Text("FOCUS STATION", size=24, weight="bold")
    
    task_input = ft.TextField(
        label="New Task",
        bgcolor="#1e293b",
        border_radius=10,
    )

    # 🟢 FIX: Using ft.FilledButton (Standard in Flet 0.80+)
    add_button = ft.FilledButton(
        content=ft.Text("ADD TASK"),
        on_click=lambda _: print("Button Clicked!")
    )

    tasks_list = ft.Column(spacing=10)

    print("--- DEBUG: UI components defined ---")

    def refresh_tasks():
        print("--- DEBUG: refresh_tasks() called ---")
        try:
            tasks_list.controls.clear()
            date_key = manager.get_key(datetime.now())
            data = manager.load_data()
            tasks = data.get(date_key, [])
            
            for t in tasks:
                if not t.get("done", False):
                    tasks_list.controls.append(
                        ft.Checkbox(label=t["text"], value=False)
                    )
            page.update()
            print(f"--- DEBUG: Successfully loaded {len(tasks)} tasks ---")
        except Exception as e:
            print(f"--- DEBUG ERROR: refresh_tasks failed: {e} ---")

    # 3. Add to Page
    try:
        page.add(
            title_text,
            ft.Divider(height=20, color="transparent"),
            task_input,
            add_button,
            ft.Divider(height=20),
            ft.Text("CURRENT TASKS:", color="#94a3b8", size=14),
            tasks_list
        )
        print("--- DEBUG: Components added to page ---")
    except Exception as e:
        print(f"--- DEBUG ERROR: page.add failed: {e} ---")

    def add_task(e):
        print("--- DEBUG: add_task() triggered ---")
        if not task_input.value: 
            print("--- DEBUG: Input empty, skipping ---")
            return
        
        try:
            # 1. Save using the shared core logic 
            date_key = manager.get_key(datetime.now())
            data = manager.load_data()
            tasks = data.get(date_key, [])
            tasks.append({"text": task_input.value, "done": False})
            data[date_key] = tasks
            manager.save_data(data)
            print(f"--- DEBUG: Task '{task_input.value}' saved to JSON ---")
            
            # 2. Clear input and refresh the list
            task_input.value = ""
            refresh_tasks()
        except Exception as ex:
            print(f"--- DEBUG ERROR: add_task failed: {ex} ---")

    # Update the button to use this new function
    add_button.on_click = add_task
    refresh_tasks()

# 🚀 Launch using the modern target syntax
print("--- DEBUG: Calling ft.app() ---")
ft.app(target=main)