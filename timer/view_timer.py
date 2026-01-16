import customtkinter as ctk
import threading
import requests
from datetime import datetime
from plyer import notification
import config

class TimerPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller # Access to main app variables
        
        self.timer_state = "IDLE"
        self.time_left = 0
        self.initial_time = 0
        self.input_string = ""

        self.setup_ui()
        # Bind keypress events from the main controller to here
        self.controller.bind("<Key>", self.handle_keypress)

    def setup_ui(self):
        self.idle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.idle_frame.pack(pady=50)

        self.new_session_btn = ctk.CTkButton(
            self.idle_frame, text="+ START NEW SESSION", command=self.enter_edit_mode,
            width=220, height=50, corner_radius=25,
            fg_color="#1E88E5", hover_color="#1565C0", font=("Roboto Medium", 15)
        )
        self.new_session_btn.pack()

        self.active_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.hint_label = ctk.CTkLabel(self.active_frame, text="Type minutes...", text_color="gray")
        self.hint_label.pack(pady=(0, 5))

        self.timer_label = ctk.CTkLabel(self.active_frame, text="00:00", font=("Roboto Mono", 80))
        self.timer_label.pack(pady=10)

        self.btn_row = ctk.CTkFrame(self.active_frame, fg_color="transparent")
        self.btn_row.pack(pady=20)

        self.main_action_btn = ctk.CTkButton(self.btn_row, text="START", command=self.handle_main_button, width=120, height=40, state="disabled", fg_color="gray")
        self.main_action_btn.grid(row=0, column=0, padx=10)

        self.cancel_btn = ctk.CTkButton(self.btn_row, text="CANCEL", command=self.cancel_session, width=100, height=40, fg_color="transparent", border_width=2, text_color="#FF5252", border_color="#FF5252")
        self.cancel_btn.grid(row=0, column=1, padx=10)

        self.update_timer()

    def handle_keypress(self, event):
        # Only process keys if this frame is visible and editing
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
        self.active_frame.pack(pady=50)
        self.timer_label.configure(text="00:00", text_color="gray")
        self.main_action_btn.configure(text="START", fg_color="gray", state="disabled")
        self.hint_label.pack(pady=(0, 5))

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

    def pause_timer(self):
        self.timer_state = "PAUSED"
        self.main_action_btn.configure(text="RESUME", fg_color="#00C853", hover_color="#009624")

    def resume_timer(self):
        self.timer_state = "RUNNING"
        self.main_action_btn.configure(text="PAUSE", fg_color="#FF9800", hover_color="#F57C00")

    def cancel_session(self):
        self.timer_state = "IDLE"
        self.active_frame.pack_forget()
        self.idle_frame.pack(pady=50)

    def update_timer(self):
        if self.timer_state == "RUNNING" and self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        elif self.timer_state == "RUNNING" and self.time_left == 0:
            self.finish_session()
        self.after(1000, self.update_timer)

    def finish_session(self):
        self.timer_state = "FINISHED"
        self.main_action_btn.configure(text="DONE", fg_color="gray", state="disabled")
        try: notification.notify(title="Focus Timer", message="Session Complete!", timeout=10)
        except: pass
        threading.Thread(target=self.save_session_to_web).start()
        self.cancel_btn.configure(text="BACK")

    def save_session_to_web(self):
        data = {
            "username": self.controller.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{self.initial_time} min",
            "tasks_done": [],
            "task_count": 0
        }
        try: requests.post(config.FIREBASE_URL, json=data)
        except: pass