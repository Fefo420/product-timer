import customtkinter as ctk
import os
import json
import config
from view_tasks import TaskManager
from view_ui import MainUI
from updater import AppUpdater #

# --- CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Focus Station v{config.CURRENT_VERSION}") # Show version in title
        self.geometry("1100x700")
        try: self.iconbitmap("icon.ico")
        except: pass
        
        self.username = "Guest"
        self.updater = AppUpdater(self.on_update_found)
        
        # Check for updates silently on startup
        self.updater.check_for_updates()

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

    # --- UPDATER CALLBACKS ---
    def on_update_found(self, found, version_str):
        """Called by updater thread when check finishes"""
        if found:
            self.new_version_str = version_str
            # Show a notification or button on the UI
            # We will hijack the login or main UI to show a banner
            self.after(0, self.show_update_banner)

    def show_update_banner(self):
        # Create a floating notification at the top
        self.update_frame = ctk.CTkFrame(self, fg_color="#10b981", height=40, corner_radius=0)
        self.update_frame.place(relx=0, rely=0, relwidth=1)
        
        msg = ctk.CTkLabel(self.update_frame, text=f"NEW VERSION AVAILABLE ({self.new_version_str})", font=("Roboto", 12, "bold"), text_color="white")
        msg.pack(side="left", padx=20, pady=5)
        
        btn = ctk.CTkButton(self.update_frame, text="UPDATE NOW", width=100, height=25, 
                            fg_color="white", text_color="#10b981", 
                            command=self.start_update)
        btn.pack(side="right", padx=20, pady=5)

    def start_update(self):
        # Replace banner with progress bar
        for widget in self.update_frame.winfo_children(): widget.destroy()
        
        self.progress_bar = ctk.CTkProgressBar(self.update_frame, width=300, progress_color="white")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.updater.perform_update(self.update_progress)

    def update_progress(self, percent):
        """Called during download"""
        if percent == -1:
            self.update_frame.configure(fg_color="#ef4444") # Red error
            return
        self.after(0, lambda: self.progress_bar.set(percent))

    # --- LOGIN SCREEN ---
    def show_login(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Roboto", 26, "bold")).pack(pady=30)
        
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

    def launch_main_ui(self):
        self.ui = MainUI(self, self, self.username, self.task_manager)
        self.ui.pack(fill="both", expand=True)
        # Ensure update banner stays on top if it exists
        if hasattr(self, 'update_frame'): self.update_frame.lift()

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()