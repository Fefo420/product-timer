import customtkinter as ctk
import json
import os
import threading
import requests
from datetime import datetime, timedelta
import config

class TaskManager:
    """Helper to manage data for both Tabs"""
    def __init__(self, controller):
        self.controller = controller

    def load_data(self):
        if not os.path.exists(config.TASKS_FILE): return {}
        try:
            with open(config.TASKS_FILE, "r") as f:
                data = json.load(f)
                return {datetime.now().strftime("%Y-%m-%d"): data} if isinstance(data, list) else data
        except: return {}

    def save_data(self, data):
        with open(config.TASKS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_key(self, date_obj):
        return date_obj.strftime("%Y-%m-%d")

    def mark_done(self, task_text, date_key=None):
        if not date_key: date_key = datetime.now().strftime("%Y-%m-%d")
        all_data = self.load_data()
        day_tasks = all_data.get(date_key, [])
        
        found = False
        for t in day_tasks:
            if t["text"] == task_text and not t.get("done", False):
                t["done"] = True
                found = True
                break
        
        if not found: day_tasks.append({"text": task_text, "done": True})
        
        all_data[date_key] = day_tasks
        self.save_data(all_data)
        threading.Thread(target=self.upload, args=(task_text,)).start()

    def delete_task(self, task_text, date_key=None):
        if not date_key: date_key = datetime.now().strftime("%Y-%m-%d")
        all_data = self.load_data()
        day_tasks = all_data.get(date_key, [])
        new_tasks = [t for t in day_tasks if t["text"] != task_text]
        all_data[date_key] = new_tasks
        self.save_data(all_data)

    def upload(self, task_name):
        data = {
            "username": self.controller.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "0 min",
            "tasks_done": [task_name],
            "task_count": 1
        }
        try: requests.post(config.FIREBASE_URL, json=data)
        except: pass

class TasksPage(ctk.CTkFrame):
    def __init__(self, parent, controller, manager):
        super().__init__(parent, fg_color="transparent")
        self.manager = manager
        self.current_view_date = datetime.now()
        self.setup_ui()

    def setup_ui(self):
        # Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(30, 20), fill="x", padx=30)
        
        ctk.CTkButton(header, text="<", width=40, height=40, corner_radius=20, fg_color="#2b2b2b", hover_color="#333333", command=lambda: self.change_day(-1)).pack(side="left")
        
        self.date_label = ctk.CTkLabel(header, text="Today", font=("Roboto", 22, "bold"), text_color="white")
        self.date_label.pack(side="left", expand=True)
        
        ctk.CTkButton(header, text=">", width=40, height=40, corner_radius=20, fg_color="#2b2b2b", hover_color="#333333", command=lambda: self.change_day(1)).pack(side="right")

        # Input Row
        input_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=12)
        input_frame.pack(pady=10, padx=30, fill="x")
        
        self.entry = ctk.CTkEntry(input_frame, placeholder_text="What needs to be done?", height=50, border_width=0, fg_color="transparent", font=("Roboto", 14), placeholder_text_color="#666666")
        self.entry.pack(side="left", fill="x", expand=True, padx=15)
        self.entry.bind("<Return>", lambda e: self.add_task())
        
        ctk.CTkButton(input_frame, text="+ ADD", width=80, height=36, corner_radius=8, command=self.add_task, fg_color="#2196F3", font=("Roboto Medium", 12)).pack(side="right", padx=10)

        # List Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)
        self.refresh()

    def change_day(self, d):
        self.current_view_date += timedelta(days=d)
        
        # 🟢 NEW LOGIC: Check if selected date is effectively "today"
        if self.current_view_date.date() == datetime.now().date():
            display_text = "Today"
        else:
            display_text = self.current_view_date.strftime("%B %d")
            
        self.date_label.configure(text=display_text)
        self.refresh()

    def add_task(self):
        text = self.entry.get()
        if not text.strip(): return
        self.entry.delete(0, "end")
        
        key = self.manager.get_key(self.current_view_date)
        data = self.manager.load_data()
        tasks = data.get(key, [])
        tasks.append({"text": text, "done": False})
        data[key] = tasks
        self.manager.save_data(data)
        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children(): w.destroy()
        key = self.manager.get_key(self.current_view_date)
        tasks = self.manager.load_data().get(key, [])
        for t in tasks:
            if not t.get("done", False): self.create_row(t["text"])

    def create_row(self, text):
        row = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b", corner_radius=8)
        row.pack(fill="x", pady=5)
        
        ctk.CTkCheckBox(row, text=text, font=("Roboto", 14), command=lambda: self.complete(row, text), fg_color="#00C853", hover_color="#009624", border_color="#606060", border_width=2).pack(side="left", padx=15, pady=15)
        
        del_btn = ctk.CTkButton(
            row, text="✕", width=30, height=30, 
            fg_color="transparent", text_color="#EF5350", hover_color="#333333",
            font=("Roboto Medium", 14),
            command=lambda: self.delete_task(row, text)
        )
        del_btn.pack(side="right", padx=10)
    
    def complete(self, widget, text):
        self.manager.mark_done(text, self.manager.get_key(self.current_view_date))
        widget.destroy()

    def delete_task(self, widget, text):
        self.manager.delete_task(text, self.manager.get_key(self.current_view_date))
        widget.destroy()