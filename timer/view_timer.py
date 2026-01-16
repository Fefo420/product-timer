import customtkinter as ctk
import threading
import requests
from datetime import datetime
from plyer import notification
import config

# Colors
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
ACCENT_COLOR = "#6366f1"
TEXT_SEC = "#94a3b8"

class TimerPage(ctk.CTkFrame):
    def __init__(self, parent, controller, task_manager):
        super().__init__(parent, fg_color="transparent") # Transparent to show UI background
        self.controller = controller
        self.task_manager = task_manager
        
        self.timer_state = "IDLE"
        self.time_left = 0
        self.initial_time = 0
        self.input_string = ""
        self.pending_tasks = set()

        self.setup_ui()
        self.controller.bind("<Key>", self.handle_keypress)

    def setup_ui(self):
        # HEADER
        ctk.CTkLabel(self, text="FOCUS TIMER", font=("Roboto Medium", 14), text_color=TEXT_SEC).pack(pady=(40, 50))

        # --- 1. IDLE STATE ---
        self.idle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.idle_frame.pack(expand=True)

        # A "Ghost" button style (Border only)
        self.new_session_btn = ctk.CTkButton(
            self.idle_frame, text="Start Session", command=self.enter_edit_mode,
            width=220, height=50, corner_radius=25,
            fg_color="transparent", border_width=2, border_color=ACCENT_COLOR, text_color="white",
            hover_color=ACCENT_COLOR, font=("Roboto Medium", 16)
        )
        self.new_session_btn.pack()

        # --- 2. ACTIVE STATE ---
        self.active_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.hint_label = ctk.CTkLabel(self.active_frame, text="Type minutes...", font=("Roboto", 16), text_color=TEXT_SEC)
        self.hint_label.pack(pady=(0, 10))

        # Ultra-Clean Font
        self.timer_label = ctk.CTkLabel(self.active_frame, text="00:00", font=("Roboto", 120, "bold"), text_color="white")
        self.timer_label.pack(pady=10)

        # Button Row
        self.btn_row = ctk.CTkFrame(self.active_frame, fg_color="transparent")
        self.btn_row.pack(pady=40)

        self.main_action_btn = ctk.CTkButton(
            self.btn_row, text="START", command=self.handle_main_button, 
            width=140, height=50, corner_radius=25, 
            state="disabled", fg_color="#334155", font=("Roboto Medium", 14)
        )
        self.main_action_btn.grid(row=0, column=0, padx=10)

        self.done_btn = ctk.CTkButton(
            self.btn_row, text="FINISH", command=self.finish_early, 
            width=140, height=50, corner_radius=25,
            fg_color="#10b981", hover_color="#059669", font=("Roboto Medium", 14)
        )
        
        self.cancel_btn = ctk.CTkButton(
            self.btn_row, text="CANCEL", command=self.cancel_session, 
            width=100, height=50, corner_radius=25,
            fg_color="transparent", text_color="#ef4444", hover_color="#1e293b",
            font=("Roboto Medium", 13)
        )
        self.cancel_btn.grid(row=0, column=2, padx=10)

        # --- 3. TASKS CARD ---
        # "Floating" Card design with border
        self.tasks_container = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=16, border_width=1, border_color="#334155")
        self.tasks_container.pack(side="bottom", fill="x", padx=60, pady=40, ipady=10)
        
        header_row = ctk.CTkFrame(self.tasks_container, fg_color="transparent")
        header_row.pack(fill="x", padx=25, pady=(15, 10))
        ctk.CTkLabel(header_row, text="SESSION GOALS", font=("Roboto Medium", 12), text_color=TEXT_SEC).pack(side="left")
        
        self.task_scroll = ctk.CTkScrollableFrame(self.tasks_container, height=120, fg_color="transparent")
        self.task_scroll.pack(fill="x", padx=15)

        self.update_timer()

    # --- LOGIC ---
    def refresh(self):
        for widget in self.task_scroll.winfo_children(): widget.destroy()
        self.pending_tasks.clear() 

        date_key = datetime.now().strftime("%Y-%m-%d")
        all_data = self.task_manager.load_data()
        day_tasks = all_data.get(date_key, [])
        active_tasks = [t for t in day_tasks if not t.get("done", False)]

        if not active_tasks:
            ctk.CTkLabel(self.task_scroll, text="No active tasks for today.", font=("Roboto", 14), text_color="#64748b").pack(pady=20)
            return

        for t in active_tasks:
            self.create_task_row(t["text"])

    def create_task_row(self, text):
        row = ctk.CTkFrame(self.task_scroll, fg_color="#0f172a", corner_radius=8) # Darker inner card
        row.pack(fill="x", pady=4, padx=5)
        
        check_var = ctk.IntVar(value=0)
        cb = ctk.CTkCheckBox(
            row, text=text, font=("Roboto", 14), variable=check_var,
            command=lambda: self.toggle_task(text, cb, check_var),
            fg_color=ACCENT_COLOR, hover_color="#4f46e5", border_color="#64748b", border_width=2,
            checkmark_color="white"
        )
        cb.pack(side="left", padx=15, pady=12)

    def toggle_task(self, text, widget, variable):
        if variable.get() == 1:
            self.pending_tasks.add(text)
            widget.configure(text_color="gray")
        else:
            if text in self.pending_tasks: self.pending_tasks.remove(text)
            widget.configure(text_color=("white", "white"))

    def handle_keypress(self, event):
        if self.timer_state != "EDITING" or not self.winfo_viewable(): return
        key = event.keysym
        if key.isdigit():
            if len(self.input_string) < 3:
                self.input_string += key
                self.update_display_while_typing()
        elif key == "BackSpace":
            self.input_string = self.input_string[:-1]
            self.update_display_while_typing()
        elif key == "Return":
            self.start_countdown()

    def update_display_while_typing(self):
        if self.input_string == "":
            self.timer_label.configure(text="00:00", text_color="#334155")
            self.main_action_btn.configure(state="disabled", fg_color="#334155")
        else:
            self.timer_label.configure(text=f"{self.input_string}:00", text_color=ACCENT_COLOR)
            self.main_action_btn.configure(state="normal", fg_color=ACCENT_COLOR)

    def enter_edit_mode(self):
        self.timer_state = "EDITING"
        self.input_string = ""
        self.idle_frame.pack_forget()
        self.active_frame.pack(expand=True)
        self.timer_label.configure(text="00:00", text_color="#334155")
        self.main_action_btn.configure(text="START", fg_color="#334155", state="disabled")
        self.hint_label.pack(pady=(0, 10))
        self.done_btn.grid_forget()
        self.refresh() 

    def handle_main_button(self):
        if self.timer_state == "EDITING": self.start_countdown()
        elif self.timer_state == "RUNNING": self.pause_timer()
        elif self.timer_state == "PAUSED": self.resume_timer()

    def start_countdown(self):
        if self.input_string == "": return
        self.timer_state = "RUNNING"
        self.initial_time = int(self.input_string)
        self.time_left = self.initial_time * 60
        self.hint_label.pack_forget()
        self.timer_label.configure(text_color="white")
        self.main_action_btn.configure(text="PAUSE", fg_color="#f59e0b", hover_color="#d97706")
        self.done_btn.grid(row=0, column=1, padx=10)

    def pause_timer(self):
        self.timer_state = "PAUSED"
        self.main_action_btn.configure(text="RESUME", fg_color="#10b981", hover_color="#059669")

    def resume_timer(self):
        self.timer_state = "RUNNING"
        self.main_action_btn.configure(text="PAUSE", fg_color="#f59e0b", hover_color="#d97706")

    def cancel_session(self):
        self.timer_state = "IDLE"
        self.active_frame.pack_forget()
        self.idle_frame.pack(expand=True)
        self.refresh()

    def finish_early(self):
        total_seconds = self.initial_time * 60
        elapsed_seconds = total_seconds - self.time_left
        actual_minutes = max(1, elapsed_seconds // 60)
        self.commit_session(actual_minutes)

    def finish_natural(self):
        self.commit_session(self.initial_time)

    def update_timer(self):
        if self.timer_state == "RUNNING" and self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        elif self.timer_state == "RUNNING" and self.time_left == 0:
            self.finish_natural()
        self.after(1000, self.update_timer)

    def commit_session(self, duration_mins):
        self.timer_state = "FINISHED"
        self.main_action_btn.configure(text="COMPLETED", fg_color="#334155", state="disabled")
        self.done_btn.grid_forget()
        self.cancel_btn.configure(text="BACK")

        for task_text in self.pending_tasks:
            self.task_manager.mark_done(task_text)

        finished_tasks_list = list(self.pending_tasks)
        try: notification.notify(title="Focus Timer", message=f"Session Done! {duration_mins} min logged.", timeout=5)
        except: pass
        threading.Thread(target=self.save_session_to_web, args=(duration_mins, finished_tasks_list)).start()
        self.after(2000, self.refresh)

    def save_session_to_web(self, duration_mins, tasks_list):
        data = {
            "username": self.controller.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{duration_mins} min",
            "tasks_done": tasks_list,
            "task_count": len(tasks_list)
        }
        try: requests.post(config.FIREBASE_URL, json=data)
        except: pass