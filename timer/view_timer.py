import customtkinter as ctk
import threading
import requests
from datetime import datetime
from plyer import notification
import config

class TimerPage(ctk.CTkFrame):
    def __init__(self, parent, controller, task_manager):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.task_manager = task_manager
        
        self.timer_state = "IDLE"
        self.time_left = 0
        self.initial_time = 0
        self.input_string = ""
        
        # Store tasks completed *during this session*
        self.pending_tasks = set() 

        self.setup_ui()
        self.controller.bind("<Key>", self.handle_keypress)

    def setup_ui(self):
        # 1. IDLE VIEW (Start Button)
        self.idle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.idle_frame.pack(pady=30)

        self.new_session_btn = ctk.CTkButton(
            self.idle_frame, text="+ START NEW SESSION", command=self.enter_edit_mode,
            width=220, height=50, corner_radius=25,
            fg_color="#1E88E5", hover_color="#1565C0", font=("Roboto Medium", 15)
        )
        self.new_session_btn.pack()

        # 2. ACTIVE VIEW (Timer & Buttons) - Initially Hidden
        self.active_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.hint_label = ctk.CTkLabel(self.active_frame, text="Type minutes...", text_color="gray")
        self.hint_label.pack(pady=(0, 5))

        self.timer_label = ctk.CTkLabel(self.active_frame, text="00:00", font=("Roboto Mono", 80))
        self.timer_label.pack(pady=10)

        self.btn_row = ctk.CTkFrame(self.active_frame, fg_color="transparent")
        self.btn_row.pack(pady=10)

        self.main_action_btn = ctk.CTkButton(self.btn_row, text="START", command=self.handle_main_button, width=100, height=40, state="disabled", fg_color="gray")
        self.main_action_btn.grid(row=0, column=0, padx=5)

        self.done_btn = ctk.CTkButton(
            self.btn_row, text="DONE", command=self.finish_early, 
            width=100, height=40, fg_color="#00C853", hover_color="#009624"
        )
        
        self.cancel_btn = ctk.CTkButton(self.btn_row, text="CANCEL", command=self.cancel_session, width=80, height=40, fg_color="transparent", border_width=2, text_color="#FF5252", border_color="#FF5252")
        self.cancel_btn.grid(row=0, column=2, padx=5)

        # 3. TASKS FOOTER (Always Visible) 🟢 MOVED HERE
        self.tasks_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tasks_frame.pack(side="bottom", fill="x", padx=40, pady=(0, 20))
        
        ctk.CTkLabel(self.tasks_frame, text="TODAY'S TASKS", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        
        self.task_scroll = ctk.CTkScrollableFrame(self.tasks_frame, height=150, fg_color="transparent")
        self.task_scroll.pack(fill="x", pady=5)

        self.update_timer()

    def refresh(self):
        """Called whenever this page is shown to reload the task list"""
        # Clear old widgets
        for widget in self.task_scroll.winfo_children():
            widget.destroy()
        
        self.pending_tasks.clear() # Reset pending state

        # Load fresh data
        date_key = datetime.now().strftime("%Y-%m-%d")
        all_data = self.task_manager.load_data()
        day_tasks = all_data.get(date_key, [])

        # Only show tasks that are NOT done yet
        active_tasks = [t for t in day_tasks if not t.get("done", False)]

        if not active_tasks:
            ctk.CTkLabel(self.task_scroll, text="No tasks pending.", text_color="gray").pack(pady=10)
            return

        for t in active_tasks:
            self.create_task_row(t["text"])

    def create_task_row(self, text):
        row = ctk.CTkFrame(self.task_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # We need a var to track state
        check_var = ctk.IntVar(value=0)
        
        cb = ctk.CTkCheckBox(
            row, text=text, font=("Arial", 14), variable=check_var,
            command=lambda: self.toggle_task(text, cb, check_var)
        )
        cb.pack(side="left", padx=5)

    def toggle_task(self, text, widget, variable):
        if variable.get() == 1:
            # Checked: Add to pending, turn gray
            self.pending_tasks.add(text)
            widget.configure(text_color="gray")
        else:
            # Unchecked: Remove from pending, restore color
            if text in self.pending_tasks:
                self.pending_tasks.remove(text)
            widget.configure(text_color=("black", "white"))

    # --- TIMER LOGIC ---
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
            self.timer_label.configure(text="00:00", text_color="gray")
            self.main_action_btn.configure(state="disabled", fg_color="gray")
        else:
            self.timer_label.configure(text=f"{self.input_string}:00", text_color="#FF9800")
            self.main_action_btn.configure(state="normal", fg_color="#00C853")

    def enter_edit_mode(self):
        self.timer_state = "EDITING"
        self.input_string = ""
        self.idle_frame.pack_forget()
        self.active_frame.pack(pady=30)
        self.timer_label.configure(text="00:00", text_color="gray")
        self.main_action_btn.configure(text="START", fg_color="gray", state="disabled")
        self.hint_label.pack(pady=(0, 5))
        self.done_btn.grid_forget()

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
        self.main_action_btn.configure(text="PAUSE", fg_color="#FF9800", hover_color="#F57C00")
        self.done_btn.grid(row=0, column=1, padx=5)

    def pause_timer(self):
        self.timer_state = "PAUSED"
        self.main_action_btn.configure(text="RESUME", fg_color="#00C853", hover_color="#009624")

    def resume_timer(self):
        self.timer_state = "RUNNING"
        self.main_action_btn.configure(text="PAUSE", fg_color="#FF9800", hover_color="#F57C00")

    def cancel_session(self):
        self.timer_state = "IDLE"
        self.active_frame.pack_forget()
        self.idle_frame.pack(pady=30)
        # Reset any pending selections if cancelled
        self.refresh()

    def finish_early(self):
        # 1. Calculate Time
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
        # 🟢 THE GRAND FINALE
        self.timer_state = "FINISHED"
        self.main_action_btn.configure(text="COMPLETED", fg_color="gray", state="disabled")
        self.done_btn.grid_forget()
        self.cancel_btn.configure(text="BACK")

        # 1. Commit Pending Tasks to Manager (Locally)
        for task_text in self.pending_tasks:
            # We bypass the manager's upload logic temporarily to batch it here if we wanted
            # But calling mark_done is safest to ensure local JSON updates
            # Note: Manager.mark_done usually uploads individually. 
            # Ideally, we update the JSON here and upload ONCE below.
            
            # Use the manager to save 'done' status to user_tasks.json
            self.task_manager.mark_done(task_text)

        # 2. Upload Session + Tasks to Firebase
        # Convert set to list
        finished_tasks_list = list(self.pending_tasks)
        
        try: notification.notify(title="Focus Timer", message=f"Done! {len(finished_tasks_list)} tasks finished.", timeout=5)
        except: pass
        
        threading.Thread(target=self.save_session_to_web, args=(duration_mins, finished_tasks_list)).start()
        
        # 3. Refresh UI (This will remove the done tasks from view)
        self.after(2000, self.refresh)

    def save_session_to_web(self, duration_mins, tasks_list):
        data = {
            "username": self.controller.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{duration_mins} min",
            "tasks_done": tasks_list,         # 🟢 Send list of tasks
            "task_count": len(tasks_list)     # 🟢 Send count
        }
        try: requests.post(config.FIREBASE_URL, json=data)
        except: pass