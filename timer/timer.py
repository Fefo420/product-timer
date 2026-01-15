import customtkinter as ctk
import requests
import json
import threading
import os  # We need this to check if the file exists
from datetime import datetime

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"
CONFIG_FILE = "user_config.json"  # This is where we save your name locally

class ModernTimer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Focus Timer")
        self.geometry("400x480")
        self.resizable(True, True)

        # Initialize Variables
        self.username = "Guest"
        self.time_left = 1500  # 25 minutes
        self.running = False

        # --- CHECK LOGIN STATUS ---
        if self.load_existing_user():
            # If we found a saved user, skip straight to the timer
            self.show_timer_screen()
        else:
            # If no user found, show the login screen
            self.show_login_screen()

    # --- LOCAL STORAGE LOGIC ---
    def load_existing_user(self):
        """Checks if a config file exists and loads the username."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", "Guest")
                    return True
            except:
                return False
        return False

    def save_user_locally(self):
        """Saves the current username to a file."""
        data = {"username": self.username}
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    # --- VIEW 1: LOGIN SCREEN ---
    def show_login_screen(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        label = ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Roboto Medium", 20))
        label.pack(pady=(80, 20))

        # Input
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter your username")
        self.username_entry.pack(pady=10)

        # Button
        btn = ctk.CTkButton(self.login_frame, text="Start Session", command=self.attempt_login)
        btn.pack(pady=20)
        
        # Allow pressing "Enter" key to login
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        name = self.username_entry.get()
        if name.strip() != "":
            self.username = name
            
            # Save the name so we don't ask again next time
            self.save_user_locally()
            
            self.login_frame.destroy() 
            self.show_timer_screen()

    # --- VIEW 2: TIMER SCREEN ---
    def show_timer_screen(self):
        # 1. Header (Shows Username)
        self.header = ctk.CTkLabel(self, text=f"SESSION: {self.username.upper()}", font=("Roboto Medium", 14), text_color="gray")
        self.header.pack(pady=(30, 10))

        # 2. Timer Display
        self.timer_label = ctk.CTkLabel(self, text="25:00", font=("Roboto Mono", 80), text_color="white")
        self.timer_label.pack(pady=20)

        # 3. Control Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)

        self.start_button = ctk.CTkButton(
            self.button_frame, text="START", command=self.start_timer,
            width=120, height=40, corner_radius=20, 
            fg_color="#00C853", hover_color="#009624", 
            font=("Roboto Medium", 14)
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.reset_button = ctk.CTkButton(
            self.button_frame, text="RESET", command=self.reset_timer,
            width=100, height=40, corner_radius=20, 
            fg_color="transparent", border_width=2, border_color="gray", 
            text_color="gray", hover_color="#333333"
        )
        self.reset_button.grid(row=0, column=1, padx=10)

        # 4. Leaderboard Button
        self.leaderboard_btn = ctk.CTkButton(
            self, text="🏆 View Leaderboard", command=self.open_leaderboard,
            width=220, height=35, fg_color="#333333", hover_color="#444444"
        )
        self.leaderboard_btn.pack(side="bottom", pady=30)

        # Start the timer loop
        self.update_timer()

    # --- LOGIC ---
    def start_timer(self):
        if not self.running:
            self.running = True
            self.start_button.configure(text="STOP", fg_color="#FF9800", hover_color="#F57C00")
        else:
            self.running = False
            self.start_button.configure(text="RESUME", fg_color="#00C853", hover_color="#009624")

    def reset_timer(self):
        self.running = False
        self.time_left = 1500
        self.timer_label.configure(text="25:00")
        self.start_button.configure(text="START", fg_color="#00C853")

    def update_timer(self):
        if self.running and self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        
        elif self.running and self.time_left == 0:
            self.running = False
            self.start_button.configure(text="FINISHED", fg_color="gray")
            threading.Thread(target=self.save_session_to_web).start()
        
        self.after(1000, self.update_timer)

    # --- FIREBASE CONNECTIONS ---
    def save_session_to_web(self):
        print(f"Saving session for {self.username}...")
        data = {
            "username": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "25 min"
        }
        try:
            requests.post(FIREBASE_URL, json=data)
            print("Saved successfully!")
        except Exception as e:
            print(f"Error saving: {e}")

    def open_leaderboard(self):
        window = ctk.CTkToplevel(self)
        window.title("Global Leaderboard")
        window.geometry("350x450")
        
        ctk.CTkLabel(window, text="Top Sessions", font=("Roboto Medium", 16)).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(window, width=300, height=350)
        scroll_frame.pack(pady=10)
        loading = ctk.CTkLabel(scroll_frame, text="Loading...")
        loading.pack()

        def fetch_data():
            try:
                response = requests.get(FIREBASE_URL)
                data = response.json()
                loading.destroy()
                
                if data:
                    sessions = list(data.values())
                    for s in reversed(sessions):
                        text = f"{s.get('username', 'Guest')}: {s.get('duration', '?')}"
                        ctk.CTkLabel(scroll_frame, text=text, font=("Roboto", 12)).pack(pady=2)
                else:
                    ctk.CTkLabel(scroll_frame, text="No sessions yet.").pack()
            except Exception as e:
                loading.configure(text=f"Error: {e}")

        threading.Thread(target=fetch_data).start()

if __name__ == "__main__":
    app = ModernTimer()
    app.mainloop()