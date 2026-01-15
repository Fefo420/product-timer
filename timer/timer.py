import customtkinter as ctk
import requests
import json
import threading
import os
from datetime import datetime
from plyer import notification

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"
CONFIG_FILE = "user_config.json"

class ModernTimer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Focus Timer")
        self.geometry("600x500") # Made it wider to fit the sidebar
        self.resizable(True, True)
        try:
            self.iconbitmap("icon.ico")
        except:
            pass

        self.username = "Guest"
        
        # Timer Logic Variables
        self.time_left = 0
        self.initial_time = 0
        self.input_string = ""
        self.timer_state = "IDLE" 

        # Key Binding
        self.bind("<Key>", self.handle_keypress)

        # Check Login
        if self.load_existing_user():
            self.setup_main_layout()
        else:
            self.show_login_screen()

    # --- LOCAL STORAGE ---
    def load_existing_user(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.username = json.load(f).get("username", "Guest")
                    return True
            except: return False
        return False

    def save_user_locally(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"username": self.username}, f)

    # --- VIEW 1: LOGIN (Full Screen) ---
    def show_login_screen(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.login_frame, text="Who is focusing?", font=("Roboto Medium", 20)).pack(pady=(80, 20))
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter your username")
        self.username_entry.pack(pady=10)
        ctk.CTkButton(self.login_frame, text="Enter", command=self.attempt_login).pack(pady=20)
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        name = self.username_entry.get()
        if name.strip():
            self.username = name
            self.save_user_locally()
            self.login_frame.destroy()
            self.setup_main_layout()

    # --- MAIN LAYOUT (Sidebar + Content) ---
    def setup_main_layout(self):
        # 1. Create Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.pack(side="left", fill="y") # Fill vertical height

        # Sidebar Title
        ctk.CTkLabel(self.sidebar, text=f"Hi, {self.username}", font=("Roboto Medium", 16)).pack(pady=(30, 20))

        # Nav Buttons
        self.btn_timer = ctk.CTkButton(self.sidebar, text="⏱ Timer", command=self.show_timer_page, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_timer.pack(pady=10, padx=10)

        self.btn_leaderboard = ctk.CTkButton(self.sidebar, text="🏆 Leaderboard", command=self.show_leaderboard_page, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_leaderboard.pack(pady=10, padx=10)

        # 2. Create Content Area (Right)
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # 3. Create the Two "Pages" (Frames) inside Content Area
        # We create them both now, but only show one at a time.
        
        # -- Page A: Timer --
        self.timer_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_timer_ui(self.timer_page_frame) # Build the timer UI inside this frame

        # -- Page B: Leaderboard --
        self.leaderboard_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_leaderboard_ui(self.leaderboard_page_frame) # Build leaderboard UI

        # Start by showing the Timer
        self.show_timer_page()

    # --- NAVIGATION LOGIC ---
    def show_timer_page(self):
        self.leaderboard_page_frame.pack_forget() # Hide Leaderboard
        self.timer_page_frame.pack(fill="both", expand=True) # Show Timer
        
        # Highlight the active button
        self.btn_timer.configure(fg_color=("gray75", "gray25"))
        self.btn_leaderboard.configure(fg_color="transparent")

    def show_leaderboard_page(self):
        self.timer_page_frame.pack_forget() # Hide Timer
        self.leaderboard_page_frame.pack(fill="both", expand=True) # Show Leaderboard
        
        # Highlight the active button
        self.btn_leaderboard.configure(fg_color=("gray75", "gray25"))
        self.btn_timer.configure(fg_color="transparent")
        
        # Refresh Data
        self.refresh_leaderboard_data()

    # --- PAGE A: TIMER UI SETUP ---
    def setup_timer_ui(self, parent_frame):
        # This is the exact same logic as before, but 'master' is now 'parent_frame'
        
        # Idle State (Button)
        self.idle_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.idle_frame.pack(pady=50)

        self.new_session_btn = ctk.CTkButton(
            self.idle_frame, text="+ START NEW SESSION", command=self.enter_edit_mode,
            width=220, height=50, corner_radius=25,
            fg_color="#1E88E5", hover_color="#1565C0", font=("Roboto Medium", 15)
        )
        self.new_session_btn.pack()

        # Active State (Timer) - Initially Hidden
        self.active_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        
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

        # Start the update loop
        self.update_timer()

    # --- PAGE B: LEADERBOARD UI SETUP ---
    def setup_leaderboard_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="Global Leaderboard", font=("Roboto Medium", 20)).pack(pady=20)
        
        self.lb_scroll = ctk.CTkScrollableFrame(parent_frame, width=350, height=350)
        self.lb_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.lb_status = ctk.CTkLabel(self.lb_scroll, text="Loading...")
        self.lb_status.pack()

    def refresh_leaderboard_data(self):
        # Clear previous list
        for widget in self.lb_scroll.winfo_children():
            widget.destroy()
            
        loading = ctk.CTkLabel(self.lb_scroll, text="Calculating scores...")
        loading.pack(pady=20)

        def fetch_and_aggregate():
            try:
                # 1. Get raw data from Firebase
                resp = requests.get(FIREBASE_URL).json()
                
                # Run UI update on main thread after processing
                self.after(0, lambda: loading.destroy())

                if not resp:
                    self.after(0, lambda: ctk.CTkLabel(self.lb_scroll, text="No data yet.").pack())
                    return

                # 2. AGGREGATE SCORES
                # Dictionary to hold totals: {'Max': 90, 'Anna': 45}
                user_totals = {}

                for entry in resp.values():
                    name = entry.get("username", "Unknown")
                    duration_str = entry.get("duration", "0 min")
                    
                    # Clean the string: "25 min" -> 25
                    try:
                        minutes = int(str(duration_str).split()[0])
                    except:
                        minutes = 0
                    
                    # Add to user's total
                    if name in user_totals:
                        user_totals[name] += minutes
                    else:
                        user_totals[name] = minutes

                # 3. SORT (Highest first)
                # Converts dict to list of tuples: [('Max', 90), ('Anna', 45)]
                sorted_users = sorted(user_totals.items(), key=lambda item: item[1], reverse=True)

                # 4. DISPLAY
                rank = 1
                for name, total_mins in sorted_users:
                    # Convert to hours/mins for display (e.g., "1h 30m")
                    hours, mins = divmod(total_mins, 60)
                    if hours > 0:
                        time_display = f"{hours}h {mins}m"
                    else:
                        time_display = f"{mins}m"
                    
                    # Define colors for Top 3
                    card_color = ("gray85", "gray20") # Default
                    text_color = "white"
                    
                    if rank == 1: text_color = "#FFD700" # Gold
                    elif rank == 2: text_color = "#C0C0C0" # Silver
                    elif rank == 3: text_color = "#CD7F32" # Bronze

                    # Create the row on the main thread
                    self.after(0, lambda n=name, t=time_display, r=rank, c=card_color, tc=text_color: self.create_leaderboard_row(n, t, r, c, tc))
                    rank += 1

            except Exception as e:
                print(e)

        threading.Thread(target=fetch_and_aggregate).start()

    def create_leaderboard_row(self, name, time_display, rank, bg_color, text_color):
        """Helper to draw the UI row safely"""
        card = ctk.CTkFrame(self.lb_scroll, fg_color=bg_color)
        card.pack(fill="x", pady=5, padx=5)
        
        # Rank Number (Left)
        ctk.CTkLabel(card, text=f"#{rank}", font=("Roboto Medium", 14), width=30, text_color=text_color).pack(side="left", padx=10)
        
        # Name (Center)
        ctk.CTkLabel(card, text=name, font=("Roboto Medium", 14), text_color=text_color).pack(side="left", padx=10)
        
        # Time (Right)
        ctk.CTkLabel(card, text=time_display, font=("Roboto", 14), text_color="gray70").pack(side="right", padx=15)

    # --- TIMER LOGIC (Same as before) ---
    def handle_keypress(self, event):
        if self.timer_state != "EDITING": return
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
        
        # Call notification BEFORE saving to web
        print("DEBUG: Calling notification function...") # <--- Debug check
        self.send_notification()
        
        threading.Thread(target=self.save_session_to_web).start()
        self.cancel_btn.configure(text="BACK")

    def save_session_to_web(self):
        data = {"username": self.username, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "duration": f"{self.initial_time} min"}
        try: requests.post(FIREBASE_URL, json=data)
        except: pass

    def send_notification(self):
        # 2. VISUAL
        try:
            notification.notify(
                title="Focus Timer",
                message="Session Complete!",
                app_name="Focus App",
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")

if __name__ == "__main__":
    app = ModernTimer()
    app.mainloop()