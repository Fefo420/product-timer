import customtkinter as ctk
import json
import os
import threading
import requests
import math
import random
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
        
        # Upload
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

# --- PAGE: TASK LIST ---
class TasksPage(ctk.CTkFrame):
    def __init__(self, parent, controller, manager):
        super().__init__(parent, fg_color="transparent")
        self.manager = manager
        self.current_view_date = datetime.now()
        self.setup_ui()

    def setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=20, fill="x")
        ctk.CTkButton(header, text="<", width=40, command=lambda: self.change_day(-1)).pack(side="left", padx=20)
        self.date_label = ctk.CTkLabel(header, text="Today", font=("Roboto Medium", 20))
        self.date_label.pack(side="left", expand=True)
        ctk.CTkButton(header, text=">", width=40, command=lambda: self.change_day(1)).pack(side="right", padx=20)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(pady=10, padx=20, fill="x")
        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Add task...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.add_task())
        ctk.CTkButton(input_frame, text="+", width=40, command=self.add_task, fg_color="#00C853").pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, width=400, height=300)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)
        self.refresh()

    def change_day(self, d):
        self.current_view_date += timedelta(days=d)
        self.date_label.configure(text=self.current_view_date.strftime("%b %d"))
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
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", pady=5)
        
        ctk.CTkCheckBox(row, text=text, command=lambda: self.complete(row, text)).pack(side="left", padx=10)
        
        del_btn = ctk.CTkButton(
            row, text="✕", width=30, height=30, 
            fg_color="transparent", text_color="#FF5252", hover_color="#333333",
            command=lambda: self.delete_task(row, text)
        )
        del_btn.pack(side="right")
    
    def complete(self, widget, text):
        self.manager.mark_done(text, self.manager.get_key(self.current_view_date))
        widget.destroy()

    def delete_task(self, widget, text):
        self.manager.delete_task(text, self.manager.get_key(self.current_view_date))
        widget.destroy()

# --- PAGE: WHEEL ---
class WheelPage(ctk.CTkFrame):
    def __init__(self, parent, controller, manager):
        super().__init__(parent, fg_color="transparent")
        self.manager = manager
        self.tasks = []
        self.angle = 0
        self.spinning = False
        self.selected = None
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Task Roulette", font=("Roboto Medium", 20)).pack(pady=10)
        self.canvas = ctk.CTkCanvas(self, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(pady=10, fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        
        self.spin_btn = ctk.CTkButton(self, text="SPIN!", command=self.start_spin, fg_color="#E91E63")
        self.spin_btn.pack(pady=10)
        
        self.res_lbl = ctk.CTkLabel(self, text="", font=("Roboto Medium", 18), text_color="#00E676")
        self.res_lbl.pack(pady=5)
        
        self.done_btn = ctk.CTkButton(self, text="Mark Done", command=self.mark_done, fg_color="#00C853")

    def refresh(self):
        key = datetime.now().strftime("%Y-%m-%d")
        data = self.manager.load_data().get(key, [])
        self.tasks = [t["text"] for t in data if not t["done"]]
        
        if self.selected and self.selected in self.tasks:
            self.res_lbl.configure(text=f"Selected: {self.selected}")
            self.done_btn.pack(pady=10)
        else:
            self.selected = None
            self.res_lbl.configure(text="")
            self.done_btn.pack_forget()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50: return
        cx, cy, r = w/2, h/2, (min(w,h)/2)-20
        
        if not self.tasks:
            self.canvas.create_text(cx, cy, text="No tasks!", fill="white")
            self.spin_btn.configure(state="disabled")
            return
            
        self.spin_btn.configure(state="normal")
        num = len(self.tasks)
        
        # 🟢 FIX: Handle visual rotation even for 1 task
        if num == 1:
             self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=config.WHEEL_COLORS[0])
             
             # Draw a marker line so we can see it spinning
             rad = math.radians(self.angle)
             mx = cx + r * math.cos(rad)
             my = cy - r * math.sin(rad)
             self.canvas.create_line(cx, cy, mx, my, fill="white", width=3)
             
             self.canvas.create_text(cx, cy, text=self.tasks[0], fill="white", font=("Arial", 14, "bold"))
        else:
            arc = 360/num
            for i, t in enumerate(self.tasks):
                start = self.angle + (i*arc)
                color = config.WHEEL_COLORS[i % len(config.WHEEL_COLORS)]
                self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=arc, fill=color)
                
                mid = math.radians(start + arc/2)
                tx, ty = cx + (r*0.6)*math.cos(mid), cy - (r*0.6)*math.sin(mid)
                self.canvas.create_text(tx, ty, text=t[:10], fill="white", font=("Arial", 10, "bold"))
        
        # Pointer
        self.canvas.create_polygon(cx+r+20, cy-10, cx+r+20, cy+10, cx+r-10, cy, fill="white")

    def start_spin(self):
        if self.spinning or not self.tasks: return
        self.spinning = True
        self.selected = None
        self.res_lbl.configure(text="")
        self.done_btn.pack_forget()
        self.speed = 20
        self.animate()

    def animate(self):
        if self.speed > 0:
            self.angle = (self.angle + self.speed) % 360
            self.draw()
            self.speed -= 0.2
            self.after(20, self.animate)
        else:
            self.spinning = False
            self.determine_winner()

    def determine_winner(self):
        norm = self.angle % 360
        if not self.tasks: return
        
        # Math works for 1 task too (360/1 = 360)
        idx = int((360 - norm) // (360/len(self.tasks))) % len(self.tasks)
        
        self.selected = self.tasks[idx]
        self.res_lbl.configure(text=f"Selected: {self.selected}")
        self.done_btn.pack(pady=10)
        # 🟢 REMOVED: notification.notify(...)

    def mark_done(self):
        if self.selected:
            self.manager.mark_done(self.selected)
            self.selected = None
            self.refresh()