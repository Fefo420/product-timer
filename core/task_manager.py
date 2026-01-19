import json
import os
import threading
import requests
from datetime import datetime
# Use relative import for the shared config
from . import config 

class TaskManager:
    """
    Shared Logic for Desktop and Mobile.
    Now independent of any specific UI framework (Tkinter/Flet).
    """
    def __init__(self, username="Guest"):
        self.username = username

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

    def upload(self, task_name):
        # 🟢 FIX: Uses self.username instead of self.controller.username
        data = {
            "username": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "0 min",
            "tasks_done": [task_name],
            "task_count": 1
        }
        try: requests.post(config.FIREBASE_URL, json=data)
        except: pass