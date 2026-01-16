import customtkinter as ctk
import os
import json
import config

# Import our new modules
from view_timer import TimerPage
from view_leaderboard import LeaderboardPage
from view_tasks import TasksPage, WheelPage, TaskManager

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("Focus Timer")
        self.geometry("750x600")
        try: self.iconbitmap("icon.ico")
        except: pass
        
        self.username = "Guest"
        self.task_manager = TaskManager(self) # Shared logic

        # Check if user already logged in
        if self.load_user():
            self.init_main_app()
        else:
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
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Roboto Medium", 20)).pack(pady=(80, 20))
        
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter your username")
        self.username_entry.pack(pady=10)
        # Allow pressing 'Enter' key
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())
        
        ctk.CTkButton(self.login_frame, text="Enter", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        name = self.username_entry.get()
        if name.strip():
            self.username = name
            self.save_user_locally() # Save so we don't ask next time
            self.login_frame.destroy() # Remove login screen
            self.init_main_app() # Start the app

    # --- MAIN APP UI ---
    def init_main_app(self):
        # 1. Sidebar
        sidebar = ctk.CTkFrame(self, width=70, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        
        # 2. Content Area
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True)
        
        # Display Greeting
        ctk.CTkLabel(self.container, text=f"Hi, {self.username}", text_color="gray").pack(anchor="ne", padx=20, pady=5)

        # 3. Instantiate Pages
        self.pages = {}
        
        # We pass 'self' as the controller
        self.pages["Timer"] = TimerPage(self.container, self, self.task_manager)
        self.pages["Leaderboard"] = LeaderboardPage(self.container, self)
        self.pages["Tasks"] = TasksPage(self.container, self, self.task_manager)
        self.pages["Wheel"] = WheelPage(self.container, self, self.task_manager)

        # 4. Nav Buttons
        self.create_nav_btn(sidebar, "⏱", "Timer")
        self.create_nav_btn(sidebar, "🏆", "Leaderboard")
        self.create_nav_btn(sidebar, "📅", "Tasks")
        self.create_nav_btn(sidebar, "🎡", "Wheel")

        self.show_page("Timer")

    def create_nav_btn(self, parent, text, page_name):
        ctk.CTkButton(parent, text=text, font=("Arial", 30), width=50, height=50, 
                      fg_color="transparent", hover_color="gray40",
                      command=lambda: self.show_page(page_name)).pack(pady=10, padx=10)

    def show_page(self, page_name):
        # Hide all
        for page in self.pages.values():
            page.pack_forget()
        
        # Show selected
        page = self.pages[page_name]
        page.pack(fill="both", expand=True)
        
        # Trigger refresh if available
        if hasattr(page, "refresh"): page.refresh()
        elif hasattr(page, "refresh_data"): page.refresh_data()
        
        self.focus()

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()