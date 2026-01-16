import customtkinter as ctk
import random
import time
import threading
from datetime import datetime

class WheelPage(ctk.CTkFrame):
    def __init__(self, parent, controller, task_manager):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.task_manager = task_manager
        self.spinning = False
        self.setup_ui()

    def setup_ui(self):
        self.header = ctk.CTkLabel(self, text="TASK ROULETTE", font=("Roboto Medium", 14), text_color="#606060")
        self.header.pack(pady=(30, 50))

        self.display_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=2, border_color="#2b2b2b")
        self.display_frame.pack(pady=20, padx=50, fill="x", ipady=40)

        self.result_label = ctk.CTkLabel(
            self.display_frame, 
            text="READY?", 
            font=("Roboto", 36, "bold"), 
            text_color="#2196F3",
            wraplength=600
        )
        self.result_label.pack(expand=True)

        self.spin_btn = ctk.CTkButton(
            self, 
            text="SPIN THE WHEEL", 
            command=self.start_spin,
            width=250, height=55, corner_radius=28,
            fg_color="#E91E63", hover_color="#C2185B", 
            font=("Roboto Medium", 15)
        )
        self.spin_btn.pack(pady=40)

        self.hint_label = ctk.CTkLabel(self, text="Picks a random task from your active list.", font=("Roboto", 12), text_color="gray")
        self.hint_label.pack(side="bottom", pady=20)

    def refresh(self):
        self.result_label.configure(text="READY?", text_color="#2196F3")
        self.spin_btn.configure(state="normal", fg_color="#E91E63")

    def start_spin(self):
        date_key = datetime.now().strftime("%Y-%m-%d")
        all_data = self.task_manager.load_data()
        day_tasks = all_data.get(date_key, [])
        active_tasks = [t["text"] for t in day_tasks if not t.get("done", False)]

        if not active_tasks:
            self.result_label.configure(text="NO TASKS!", text_color="#EF5350")
            return

        self.spin_btn.configure(state="disabled", fg_color="#424242")
        self.spinning = True
        threading.Thread(target=self.run_animation, args=(active_tasks,)).start()

    def run_animation(self, tasks):
        delay = 0.05
        for _ in range(25):
            selected = random.choice(tasks)
            self.result_label.configure(text=selected, text_color="#ffffff")
            time.sleep(delay)
            delay += 0.01
        
        winner = random.choice(tasks)
        self.result_label.configure(text=f"WINNER:\n{winner}", text_color="#00C853")
        self.spin_btn.configure(state="normal", fg_color="#E91E63")