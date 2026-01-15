import customtkinter as ctk
import requests  # This is what we use to talk to the URL
import json
import threading
from datetime import datetime

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# 🔴 REPLACE THIS WITH YOUR ACTUAL FIREBASE URL
# Make sure to keep the "/leaderboard.json" at the end!
FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"

class ModernTimer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Focus Timer + Web Leaderboard")
        self.geometry("400x480")
        self.resizable(True, True)

        self.time_left = 1500  # 25 minutes default
        self.running = False
        # --- UI LAYOUT ---
        
        # 1. Header
        self.header = ctk.CTkLabel(self, text="FOCUS SESSION", font=("Roboto Medium", 14), text_color="gray")
        self.header.pack(pady=(30, 10))

        # 2. Timer Display
        self.timer_label = ctk.CTkLabel(
            self, 
            text="00:00", 
            font=("Roboto Mono", 80), 
            text_color="white"
        )
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

        self.update_timer()

    # --- TIMER LOGIC ---

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
            # Save to web in background
            threading.Thread(target=self.save_session_to_web).start()
        
        self.after(1000, self.update_timer)

    # --- WEB / FIREBASE LOGIC ---

    def save_session_to_web(self):
        print("Saving to database...")
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "25 min"
        }
        
        try:
            # We use POST to add a new entry to the list
            response = requests.post(FIREBASE_URL, json=data)
            if response.status_code == 200:
                print("Successfully saved!")
            else:
                print(f"Error saving: {response.status_code}")
        except Exception as e:
            print(f"Connection error: {e}")

    def open_leaderboard(self):
        window = ctk.CTkToplevel(self)
        window.title("Global Leaderboard")
        window.geometry("350x450")
        
        label = ctk.CTkLabel(window, text="Top Sessions", font=("Roboto Medium", 16))
        label.pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(window, width=300, height=350)
        scroll_frame.pack(pady=10)

        loading_label = ctk.CTkLabel(scroll_frame, text="Loading...")
        loading_label.pack()

        # Fetch data in background
        def fetch_data():
            try:
                response = requests.get(FIREBASE_URL)
                data = response.json()
                
                loading_label.destroy()
                
                if data:
                    # Firebase returns a dictionary of keys { "-N728...": {data}, ... }
                    # We convert it to a list so we can reverse it
                    sessions_list = list(data.values())
                    
                    # Reverse to show newest first
                    for session in reversed(sessions_list):
                        row = ctk.CTkLabel(
                            scroll_frame, 
                            text=f"{session.get('date')}  —  {session.get('duration')}",
                            font=("Roboto", 12)
                        )
                        row.pack(pady=2)
                else:
                    ctk.CTkLabel(scroll_frame, text="No sessions yet.").pack()

            except Exception as e:
                loading_label.configure(text=f"Connection Error:\n{e}")

        threading.Thread(target=fetch_data).start()

if __name__ == "__main__":
    app = ModernTimer()
    app.mainloop()