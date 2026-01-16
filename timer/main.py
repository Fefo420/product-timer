import customtkinter as ctk
import os
import json
import config
from view_tasks import TaskManager
from view_ui import MainUI # Import our new UI engine

# --- CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Focus Station")
        self.geometry("1100x700")
        try: self.iconbitmap("icon.ico")
        except: pass
        
        self.username = "Guest"
        
        # Initialize Logic
        if self.load_user():
            self.task_manager = TaskManager(self)
            self.launch_main_ui()
        else:
            self.task_manager = TaskManager(self)
            self.show_login()

    def load_user(self):
        if os.path.exists(config.CONFIG_FILE):
            try:
                with open(config.CONFIG_FILE) as f:
                    self.username = json.load(f).get("username", "Guest")
                    return True
            except: pass
        return False

    def save_user_locally(self):
        with open(config.CONFIG_FILE, "w") as f:
            json.dump({"username": self.username}, f)

    # --- LOGIN SCREEN ---
    def show_login(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Futura", 26, "bold")).pack(pady=30)
        
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter username...", width=300, height=50, font=("Arial", 14))
        self.username_entry.pack(pady=10)
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())
        
        ctk.CTkButton(self.login_frame, text="ENTER STATION", width=300, height=50, font=("Arial", 14, "bold"), fg_color="#1E88E5", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        name = self.username_entry.get()
        if name.strip():
            self.username = name
            self.save_user_locally()
            self.login_frame.destroy()
            self.launch_main_ui()

    # --- LAUNCHER ---
    def launch_main_ui(self):
        # Create the UI Shell and fill the screen
        self.ui = MainUI(self, self, self.username, self.task_manager)
        self.ui.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()