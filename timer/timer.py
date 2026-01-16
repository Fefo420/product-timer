import customtkinter as ctk
import requests
import json
import threading
import os
import math
import random
from datetime import datetime
from plyer import notification
from datetime import datetime, timedelta

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
        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, width=70, corner_radius=0)
        self.sidebar.pack(side="left", fill="y") 
        self.sidebar.pack_propagate(False)

        ctk.CTkFrame(self.sidebar, height=30, fg_color="transparent").pack()

        # Nav Buttons
        self.btn_timer = ctk.CTkButton(self.sidebar, text="⏱", font=("Arial", 30), command=self.show_timer_page, width=50, height=50, corner_radius=10, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        self.btn_timer.pack(pady=10, padx=10)

        self.btn_leaderboard = ctk.CTkButton(self.sidebar, text="🏆", font=("Arial", 30), command=self.show_leaderboard_page, width=50, height=50, corner_radius=10, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        self.btn_leaderboard.pack(pady=10, padx=10)

        self.btn_tasks = ctk.CTkButton(self.sidebar, text="📅", font=("Arial", 30), command=self.show_tasks_page, width=50, height=50, corner_radius=10, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        self.btn_tasks.pack(pady=10, padx=10)
        
        # 🟢 NEW: Wheel Button
        self.btn_wheel = ctk.CTkButton(self.sidebar, text="🎡", font=("Arial", 30), command=self.show_wheel_page, width=50, height=50, corner_radius=10, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        self.btn_wheel.pack(pady=10, padx=10)

        # 2. Content Area
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.greeting_label = ctk.CTkLabel(self.content_area, text=f"Hi, {self.username}", font=("Roboto Medium", 14), text_color="gray")
        self.greeting_label.pack(anchor="ne", padx=20, pady=10)

        # 3. Create ALL Pages
        self.timer_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_timer_ui(self.timer_page_frame) 

        self.leaderboard_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_leaderboard_ui(self.leaderboard_page_frame) 

        self.tasks_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_tasks_ui(self.tasks_page_frame)

        # 🟢 NEW: Wheel Page Frame
        self.wheel_page_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.setup_wheel_ui(self.wheel_page_frame)

        self.show_timer_page()
    

    # --- NAVIGATION LOGIC ---
    def show_timer_page(self):
        self._hide_all_pages()
        self.timer_page_frame.pack(fill="both", expand=True) 
        self.btn_timer.configure(fg_color=("gray75", "gray25"))
        self.focus()

    def show_leaderboard_page(self):
        self._hide_all_pages()
        self.leaderboard_page_frame.pack(fill="both", expand=True) 
        self.btn_leaderboard.configure(fg_color=("gray75", "gray25"))
        self.refresh_leaderboard_data()

    def show_tasks_page(self):
        self._hide_all_pages()
        self.tasks_page_frame.pack(fill="both", expand=True)
        self.btn_tasks.configure(fg_color=("gray75", "gray25"))

    def _hide_all_pages(self):
        """Helper to hide everything before showing a new page"""
        self.timer_page_frame.pack_forget()
        self.leaderboard_page_frame.pack_forget()
        self.tasks_page_frame.pack_forget()
        
        # Reset buttons
        self.btn_timer.configure(fg_color="transparent")
        self.btn_leaderboard.configure(fg_color="transparent")
        self.btn_tasks.configure(fg_color="transparent")

    def show_wheel_page(self):
        self._hide_all_pages()
        self.wheel_page_frame.pack(fill="both", expand=True)
        self.btn_wheel.configure(fg_color=("gray75", "gray25"))
        self.refresh_wheel_data() # Load fresh tasks

    # Update show_tasks_page to refresh list when clicked
    def show_tasks_page(self):
        self._hide_all_pages()
        self.tasks_page_frame.pack(fill="both", expand=True)
        self.btn_tasks.configure(fg_color=("gray75", "gray25"))
        self.refresh_task_list() # Ensure we see updates from wheel

    def _hide_all_pages(self):
        self.timer_page_frame.pack_forget()
        self.leaderboard_page_frame.pack_forget()
        self.tasks_page_frame.pack_forget()
        self.wheel_page_frame.pack_forget() # Hide wheel too
        
        self.task_entry.delete(0, "end")
        
        self.btn_timer.configure(fg_color="transparent")
        self.btn_leaderboard.configure(fg_color="transparent")
        self.btn_tasks.configure(fg_color="transparent")
        self.btn_wheel.configure(fg_color="transparent")

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
        for widget in self.lb_scroll.winfo_children():
            widget.destroy()
            
        loading = ctk.CTkLabel(self.lb_scroll, text="Calculating scores...")
        loading.pack(pady=20)

        def fetch_and_aggregate():
            try:
                resp = requests.get(FIREBASE_URL).json()
                self.after(0, lambda: loading.destroy())

                if not resp:
                    self.after(0, lambda: ctk.CTkLabel(self.lb_scroll, text="No data yet.").pack())
                    return

                # Structure: 'User': {'minutes': 0, 'tasks': 0, 'history': {}} <--- History is now a DICT
                user_stats = {}

                for entry in resp.values():
                    name = entry.get("username", "Unknown")
                    duration_str = entry.get("duration", "0 min")
                    session_tasks = entry.get("tasks_done", []) 
                    session_task_count = entry.get("task_count", 0) 
                    
                    try: minutes = int(str(duration_str).split()[0])
                    except: minutes = 0
                    
                    if name not in user_stats:
                        user_stats[name] = {'minutes': 0, 'tasks': 0, 'history': {}} # Initialize as Dict
                    
                    user_stats[name]['minutes'] += minutes
                    user_stats[name]['tasks'] += session_task_count
                    
                    # 🟢 NEW LOGIC: Count occurrences
                    for t in session_tasks:
                        current_count = user_stats[name]['history'].get(t, 0)
                        user_stats[name]['history'][t] = current_count + 1

                # SORT
                sorted_users = sorted(user_stats.items(), key=lambda item: item[1]['minutes'], reverse=True)

                # DISPLAY
                rank = 1
                for name, stats in sorted_users:
                    total_mins = stats['minutes']
                    total_tasks = stats['tasks']
                    history = stats['history'] # This is now {'TaskA': 1, 'TaskB': 2}
                    
                    hours, mins = divmod(total_mins, 60)
                    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    
                    card_color = ("gray85", "gray20")
                    text_color = "white"
                    if rank == 1: text_color = "#FFD700" 
                    elif rank == 2: text_color = "#C0C0C0" 
                    elif rank == 3: text_color = "#CD7F32" 

                    self.after(0, lambda n=name, t=time_str, tc=total_tasks, h=history, r=rank, c=card_color, txt=text_color: 
                               self.create_leaderboard_row(n, t, tc, h, r, c, txt))
                    rank += 1

            except Exception as e:
                print(f"Leaderboard Error: {e}")

        threading.Thread(target=fetch_and_aggregate).start()

    def create_leaderboard_row(self, name, time_str, task_count, history, rank, bg_color, text_color):
        # Create the card frame
        card = ctk.CTkFrame(self.lb_scroll, fg_color=bg_color)
        card.pack(fill="x", pady=5, padx=5)
        
        # --- CLICK EVENT BINDING ---
        # We bind the click to the card AND all labels inside it
        def on_click(event):
            self.show_user_details(name, time_str, task_count, history)

        card.bind("<Button-1>", on_click) # Left click

        # Rank
        l1 = ctk.CTkLabel(card, text=f"#{rank}", font=("Roboto Medium", 14), width=30, text_color=text_color)
        l1.pack(side="left", padx=10)
        l1.bind("<Button-1>", on_click)
        
        # Name
        l2 = ctk.CTkLabel(card, text=name, font=("Roboto Medium", 14), text_color=text_color)
        l2.pack(side="left", padx=5)
        l2.bind("<Button-1>", on_click)
        
        # Time (Right side)
        l3 = ctk.CTkLabel(card, text=time_str, font=("Roboto", 14), text_color="gray70")
        l3.pack(side="right", padx=15)
        l3.bind("<Button-1>", on_click)

        # Task Count (Middle-ish)
        # We display it as "5 ✅"
        l4 = ctk.CTkLabel(card, text=f"{task_count} tasks", font=("Roboto", 12), text_color="gray50")
        l4.pack(side="right", padx=10)
        l4.bind("<Button-1>", on_click)

    def show_user_details(self, name, time_str, task_count, history):
        # Create a new top-level window
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"{name}'s Profile")
        detail_window.geometry("300x400")
        detail_window.attributes('-topmost', True)
        detail_window.lift()

        # Header
        ctk.CTkLabel(detail_window, text=name, font=("Roboto Medium", 24)).pack(pady=(20, 5))
        ctk.CTkLabel(detail_window, text="Focus Stats", text_color="gray").pack(pady=(0, 20))

        # Stats Grid
        stats_frame = ctk.CTkFrame(detail_window, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20)
        
        f1 = ctk.CTkFrame(stats_frame, fg_color=("gray90", "gray20"))
        f1.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(f1, text="Time", font=("Arial", 12)).pack(pady=(5,0))
        ctk.CTkLabel(f1, text=time_str, font=("Arial", 16, "bold"), text_color="#00C853").pack(pady=(0,5))

        f2 = ctk.CTkFrame(stats_frame, fg_color=("gray90", "gray20"))
        f2.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(f2, text="Tasks Done", font=("Arial", 12)).pack(pady=(5,0))
        ctk.CTkLabel(f2, text=str(task_count), font=("Arial", 16, "bold"), text_color="#1E88E5").pack(pady=(0,5))

        # List
        ctk.CTkLabel(detail_window, text="Completed Tasks", font=("Roboto Medium", 14)).pack(pady=(30, 10))
        
        scroll = ctk.CTkScrollableFrame(detail_window, width=250, height=150)
        scroll.pack()

        if not history:
            ctk.CTkLabel(scroll, text="No tasks recorded.", text_color="gray").pack(pady=20)
        else:
            # 🟢 NEW LOGIC: Iterate through dictionary items
            for task_name, count in history.items():
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                # Format text: "Homework" OR "Homework x3"
                display_text = f"✅ {task_name}"
                if count > 1:
                    display_text += f" (x{count})"
                    
                ctk.CTkLabel(row, text=display_text, anchor="w", font=("Roboto", 12)).pack(fill="x", padx=5)

    # --- PAGE C: TASKS UI SETUP ---
    def setup_tasks_ui(self, parent_frame):
        # 1. Header (Date Navigator)
        header_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        header_frame.pack(pady=20, fill="x")

        # Previous Day Button
        ctk.CTkButton(header_frame, text="<", width=40, command=lambda: self.change_day(-1), fg_color="transparent", border_width=1).pack(side="left", padx=20)
        
        # Date Label (We save it as a class variable to update it later)
        self.current_view_date = datetime.now() # Start at today
        self.date_label = ctk.CTkLabel(header_frame, text=self.get_date_display(), font=("Roboto Medium", 20))
        self.date_label.pack(side="left", expand=True)

        # Next Day Button
        ctk.CTkButton(header_frame, text=">", width=40, command=lambda: self.change_day(1), fg_color="transparent", border_width=1).pack(side="right", padx=20)

        # 2. Input Area
        input_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        input_frame.pack(pady=10, padx=20, fill="x")

        self.task_entry = ctk.CTkEntry(input_frame, placeholder_text="Add task for this day...")
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.task_entry.bind("<Return>", lambda event: self.add_task()) 

        add_btn = ctk.CTkButton(input_frame, text="+", width=40, command=self.add_task, fg_color="#00C853", hover_color="#009624")
        add_btn.pack(side="right")

        # 3. Scrollable List Area
        self.tasks_scroll = ctk.CTkScrollableFrame(parent_frame, width=400, height=300)
        self.tasks_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Load initial data
        self.refresh_task_list()


    # --- PAGE D: SPINNING WHEEL UI ---
    def setup_wheel_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="Task Roulette", font=("Roboto Medium", 20)).pack(pady=10)
        
        # 🟢 CHANGE: Remove fixed width/height so it fills the space
        self.wheel_canvas = ctk.CTkCanvas(parent_frame, bg="#2b2b2b", highlightthickness=0)
        self.wheel_canvas.pack(pady=10, fill="both", expand=True)
        
        # 🟢 NEW: Watch for resize events
        self.wheel_canvas.bind("<Configure>", lambda e: self.draw_wheel())
        
        self.spin_btn = ctk.CTkButton(parent_frame, text="SPIN!", command=self.start_spin, width=150, height=40, font=("Roboto Medium", 16), fg_color="#E91E63", hover_color="#C2185B")
        self.spin_btn.pack(pady=10)

        self.result_label = ctk.CTkLabel(parent_frame, text="", font=("Roboto Medium", 18), text_color="#00E676")
        self.result_label.pack(pady=5)
        
        self.wheel_done_btn = ctk.CTkButton(parent_frame, text="Mark as Done & Remove", command=self.complete_wheel_task, fg_color="#00C853", hover_color="#009624")
        
        self.wheel_tasks = []
        self.wheel_colors = ["#EF5350", "#AB47BC", "#5C6BC0", "#29B6F6", "#26A69A", "#9CCC65", "#FFA726", "#FF7043"]
        self.current_angle = 0
        self.is_spinning = False
        self.selected_task = None

    def refresh_wheel_data(self):
        """Loads incomplete tasks for TODAY, but remembers the winner if one exists"""
        all_data = self.load_all_data()
        date_key = self.get_date_key()
        todays_list = all_data.get(date_key, [])
        
        # 1. Get current list of undone tasks
        current_tasks = [t["text"] for t in todays_list if not t["done"]]
        self.wheel_tasks = current_tasks
        
        # 2. Check if we have a "Selected Task" pending
        if self.selected_task:
            # Verify the selected task is still in the list (in case you deleted it in the Task tab)
            if self.selected_task in self.wheel_tasks:
                # Restoring the "Winner" view
                self.result_label.configure(text=f"Selected: {self.selected_task}")
                self.wheel_done_btn.pack(pady=10)
            else:
                # The task was deleted elsewhere, so reset the view
                self.selected_task = None
                self.result_label.configure(text="")
                self.wheel_done_btn.pack_forget()
        else:
            # No active selection, clean slate
            self.result_label.configure(text="")
            self.wheel_done_btn.pack_forget()

        self.draw_wheel()

    def draw_wheel(self):
        self.wheel_canvas.delete("all")
        
        # 🟢 NEW: Get actual size dynamically
        w = self.wheel_canvas.winfo_width()
        h = self.wheel_canvas.winfo_height()
        
        # Prevent drawing if window is too small (startup glitch prevention)
        if w < 50 or h < 50: return

        cx, cy = w / 2, h / 2
        # Radius is half the smallest side, minus padding
        r = (min(w, h) / 2) - 20 
        
        if not self.wheel_tasks:
            # Empty State
            self.wheel_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="gray", width=2)
            self.wheel_canvas.create_text(cx, cy, text="No tasks left!", fill="white", font=("Arial", 14))
            self.spin_btn.configure(state="disabled")
            return

        self.spin_btn.configure(state="normal")
        num_tasks = len(self.wheel_tasks)
        
        # 🟢 FIX: Single Task Case (Draw Circle instead of Arc)
        if num_tasks == 1:
            self.wheel_canvas.create_oval(
                cx-r, cy-r, cx+r, cy+r,
                fill=self.wheel_colors[0], outline="#2b2b2b"
            )
            self.wheel_canvas.create_text(cx, cy, text=self.wheel_tasks[0], fill="white", font=("Arial", 14, "bold"))
            
            # Draw Pointer (Fixed at right side)
            self.wheel_canvas.create_polygon(cx+r+10, cy-10, cx+r+10, cy+10, cx+r-20, cy, fill="white")
            return

        # Multiple Tasks Case
        arc_size = 360 / num_tasks
        
        for i, task in enumerate(self.wheel_tasks):
            start_angle = self.current_angle + (i * arc_size)
            color = self.wheel_colors[i % len(self.wheel_colors)]
            
            self.wheel_canvas.create_arc(
                cx-r, cy-r, cx+r, cy+r,
                start=start_angle, extent=arc_size,
                fill=color, outline="#2b2b2b"
            )
            
            # Dynamic Text Position
            mid_angle_rad = math.radians(start_angle + arc_size/2)
            tx = cx + (r * 0.6) * math.cos(mid_angle_rad)
            ty = cy - (r * 0.6) * math.sin(mid_angle_rad) 
            
            display_text = task[:10] + "..." if len(task) > 10 else task
            # Scale font slightly based on radius
            font_size = max(8, int(r / 10))
            self.wheel_canvas.create_text(tx, ty, text=display_text, fill="white", font=("Arial", font_size, "bold"))

        # Draw Pointer (Dynamic Position)
        # Calculates the right edge of the circle: cx + r
        px = cx + r
        self.wheel_canvas.create_polygon(px+20, cy-10, px+20, cy+10, px-10, cy, fill="white")

    def start_spin(self):
        if self.is_spinning or not self.wheel_tasks: return
        
        # 🟢 NEW: Clear the stored selection when starting a NEW spin
        self.selected_task = None 
        
        self.is_spinning = True
        self.result_label.configure(text="")
        self.wheel_done_btn.pack_forget()
        
        self.spin_speed = 20
        self.animate_spin()

    def animate_spin(self):
        if self.spin_speed > 0:
            self.current_angle = (self.current_angle + self.spin_speed) % 360
            self.draw_wheel()
            
            # Decelerate
            self.spin_speed -= 0.2
            
            # Loop
            self.after(20, self.animate_spin)
        else:
            self.is_spinning = False
            self.determine_winner()

    def determine_winner(self):
        # In Tkinter, 0 degrees is 3 o'clock (Right). 
        # Our pointer is at 0.
        # We need to find which slice covers angle 360 (or 0)
        
        # Normalize angle to 0-360
        normalized_angle = self.current_angle % 360
        
        # The slice "under" the pointer is calculated by logic:
        # If wheel is at angle A, Slice 0 is at [A, A+size].
        # We want to know which Slice N contains 360 (or 0).
        
        num_tasks = len(self.wheel_tasks)
        arc_size = 360 / num_tasks
        
        # Math trick to find the index under the pointer
        pointer_pos = 360 - normalized_angle
        winner_index = int(pointer_pos // arc_size) % num_tasks
        
        self.selected_task = self.wheel_tasks[winner_index]
        self.result_label.configure(text=f"Selected: {self.selected_task}")
        self.wheel_done_btn.pack(pady=10)
        
        self.send_notification("Spin Complete", f"Your task is: {self.selected_task}")

    def complete_wheel_task(self):
        if self.selected_task:
            # 1. Mark it done in the database
            # Note: We pass None for the widget because the wheel has no checkbox to destroy
            self.mark_task_complete(None, self.selected_task)
            
            # 2. 🟢 FIX: Explicitly forget the selection
            # This tells the refresh function: "Don't show the winner button anymore"
            self.selected_task = None
            
            # 3. Refresh the wheel to remove the slice
            self.refresh_wheel_data()

    def send_notification(self, title, msg):
        try: notification.notify(title=title, message=msg, timeout=5)
        except: pass

    # --- DATE LOGIC ---
    def get_date_key(self):
        """Returns string key for storage: '2023-10-27'"""
        return self.current_view_date.strftime("%Y-%m-%d")

    def get_date_display(self):
        """Returns pretty text: 'Fri, Oct 27'"""
        # If it's today, show "Today"
        if self.current_view_date.date() == datetime.now().date():
            return f"Today ({self.current_view_date.strftime('%b %d')})"
        return self.current_view_date.strftime("%a, %b %d")

    def change_day(self, days):
        """Moves the view backward or forward"""
        self.current_view_date += timedelta(days=days)
        self.date_label.configure(text=self.get_date_display())
        self.refresh_task_list()

    # --- TASK ACTIONS ---
    def add_task(self):
        task_text = self.task_entry.get()
        if not task_text.strip(): return
        
        self.create_task_row(task_text, False)
        self.task_entry.delete(0, "end")
        self.save_current_day_tasks()

    def create_task_row(self, text, is_done):
        # If we are creating rows from the file, DON'T show the done ones
        if is_done:
            return

        row = ctk.CTkFrame(self.tasks_scroll, fg_color="transparent")
        row.pack(fill="x", pady=5)

        # Checkbox
        var = ctk.BooleanVar(value=is_done)
        checkbox = ctk.CTkCheckBox(
            row, text=text, variable=var, 
            font=("Roboto", 14),
            # 🟢 CHANGE: Use a specific function for completion
            command=lambda: self.mark_task_complete(row, text) 
        )
        checkbox.pack(side="left", padx=10)

        # Delete Button
        del_btn = ctk.CTkButton(
            row, text="✕", width=30, height=30, 
            fg_color="transparent", text_color="#FF5252", hover_color="#333333",
            command=lambda: self.delete_task(row)
        )
        del_btn.pack(side="right")

    def mark_task_complete(self, row_widget, task_text):
        """Marks task as done. row_widget can be None (if called from Wheel)."""
        all_data = self.load_all_data()
        date_key = self.get_date_key()
        day_tasks = all_data.get(date_key, [])

        found = False
        for t in day_tasks:
            # Find the first task that matches the text and isn't done yet
            if t["text"] == task_text and not t.get("done", False):
                t["done"] = True
                found = True
                break
        
        # Safety: If task somehow missing, add it as done
        if not found:
            day_tasks.append({"text": task_text, "done": True})

        all_data[date_key] = day_tasks
        
        with open("user_tasks.json", "w") as f:
            json.dump(all_data, f, indent=4)

        # Remove from UI (If it's a checkbox row)
        if row_widget:
            row_widget.destroy()
            
        # Upload to profile
        threading.Thread(target=self.upload_single_task_to_web, args=(task_text,)).start()

    def delete_task(self, row_widget):
        row_widget.destroy()
        self.save_current_day_tasks()

    # --- STORAGE (UPDATED FOR DATES) ---
    def load_all_data(self):
        """Helper to load the whole JSON file safely"""
        if not os.path.exists("user_tasks.json"): return {}
        try:
            with open("user_tasks.json", "r") as f:
                data = json.load(f)
                
                # 🔴 FIX: Check if we loaded an old List (Old format)
                if isinstance(data, list):
                    # We found old data! Let's migrate it to "Today" so it doesn't crash
                    print("Migrating old task list to new date format...")
                    today_key = datetime.now().strftime("%Y-%m-%d")
                    return {today_key: data}
                
                # If it's already a dictionary (New format), just return it
                return data
        except: return {}

    def refresh_task_list(self):
        """Clears UI and loads tasks ONLY for the selected date"""
        # Clear UI
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        # Load from file
        all_data = self.load_all_data()
        date_key = self.get_date_key()
        
        # Get list for this specific day (default to empty list)
        day_tasks = all_data.get(date_key, [])
        
        for t in day_tasks:
            self.create_task_row(t["text"], t["done"])

    def save_current_day_tasks(self):
        """Saves visible tasks while preserving hidden completed ones"""
        # 1. Load existing data to preserve 'done' tasks
        all_data = self.load_all_data()
        date_key = self.get_date_key()
        existing_tasks = all_data.get(date_key, [])
        
        # Keep ONLY the completed tasks from the file (the hidden ones)
        saved_tasks = [t for t in existing_tasks if t.get("done", False)]
        
        # 2. Add the current Visible tasks from UI (the pending ones)
        for row in self.tasks_scroll.winfo_children():
            for widget in row.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    # We assume visible tasks are NOT done (since done ones are removed)
                    saved_tasks.append({"text": widget.cget("text"), "done": False})
        
        # 3. Save combined list
        all_data[date_key] = saved_tasks
        
        with open("user_tasks.json", "w") as f:
            json.dump(all_data, f, indent=4)


    # --- TASK PERSISTENCE (Save/Load) ---
    def upload_single_task_to_web(self, task_name):
        """Sends just ONE task to the cloud immediately"""
        data = {
            "username": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "0 min",     # No time added
            "tasks_done": [task_name],
            "task_count": 1          # Count increases by 1
        }
        try: 
            requests.post(FIREBASE_URL, json=data)
            print(f"DEBUG: Uploaded task '{task_name}'")
        except Exception as e:
            print(f"Upload failed: {e}")

    def get_all_tasks(self):
        """Scrapes the UI to find all current tasks"""
        tasks = []
        for row in self.tasks_scroll.winfo_children():
            # Find the checkbox inside the row to get text and state
            for widget in row.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    tasks.append({"text": widget.cget("text"), "done": widget.get()})
        return tasks

    def save_tasks(self):
        tasks = self.get_all_tasks()
        with open("user_tasks.json", "w") as f:
            json.dump(tasks, f)

    def load_tasks(self):
        if os.path.exists("user_tasks.json"):
            try:
                with open("user_tasks.json", "r") as f:
                    tasks = json.load(f)
                    for t in tasks:
                        self.create_task_row(t["text"], t["done"])
            except: pass

    # --- TIMER LOGIC (Same as before) ---
    def handle_keypress(self, event):
        if self.timer_state != "EDITING" or not self.timer_page_frame.winfo_viewable():
            return

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
        """Uploads ONLY the time duration (Tasks are handled separately now)"""
        data = {
            "username": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{self.initial_time} min",
            "tasks_done": [],  # Empty, because tasks are uploaded individually now
            "task_count": 0
        }
        try: requests.post(FIREBASE_URL, json=data)
        except: pass

        # 2. Prepare Payload
        data = {
            "username": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{self.initial_time} min",
            "tasks_done": completed_tasks,       # List of task names
            "task_count": len(completed_tasks)   # Number of tasks
        }

        # 3. Send to Firebase
        try: 
            requests.post(FIREBASE_URL, json=data)
        except Exception as e:
            print(f"Upload failed: {e}")

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