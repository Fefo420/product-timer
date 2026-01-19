import customtkinter as ctk
from view_timer import TimerPage
from view_tasks import TasksPage
from view_wheel import WheelPage
from view_leaderboard import LeaderboardPage

# --- THEME COLORS ---
# We define them here to keep everything consistent
BG_COLOR = "#0f172a"        # Rich Dark Slate (Main BG)
SIDEBAR_COLOR = "#020617"   # Almost Black Slate
ACCENT_COLOR = "#6366f1"    # Indigo 500 (Vibrant, Professional)
TEXT_PRIMARY = "#f8fafc"    # White-ish
TEXT_SECONDARY = "#94a3b8"  # Muted Slate

class MainUI(ctk.CTkFrame):
    def __init__(self, parent, controller, username, task_manager):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.username = username
        self.task_manager = task_manager
        
        self.current_page_name = None
        self.pages = {}
        
        self.setup_layout()
        self.init_pages()
        self.show_page("Timer", animate=False)

    def setup_layout(self):
        # 1. SIDEBAR (Fixed Left)
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(50, 40))
        
        # A simple colored box next to the logo to add "brand" feel
        ctk.CTkLabel(logo_frame, text="  ", fg_color=ACCENT_COLOR, width=5, height=30, corner_radius=2).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(logo_frame, text="FOCUS STATION", font=("Roboto", 20, "bold"), text_color="white").pack(side="left")

        # Nav Buttons
        self.nav_buttons = {}
        self.create_nav_btn("TIMER", "Timer")
        self.create_nav_btn("TASKS", "Tasks")
        self.create_nav_btn("WHEEL", "Wheel")
        self.create_nav_btn("RANKS", "Leaderboard")

        # User Profile (Floating Card at bottom)
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155")
        user_frame.pack(side="bottom", fill="x", padx=20, pady=30, ipady=10)
        
        ctk.CTkLabel(user_frame, text="LOGGED IN AS", font=("Roboto", 10, "bold"), text_color=TEXT_SECONDARY).pack(pady=(5,0))
        ctk.CTkLabel(user_frame, text=self.username.upper(), font=("Roboto", 13, "bold"), text_color=ACCENT_COLOR).pack(pady=(0,5))

        # 2. CONTENT CONTAINER
        self.container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.container.pack(side="left", fill="both", expand=True)

    def init_pages(self):
        # Pass color constants so pages match
        self.pages["Timer"] = TimerPage(self.container, self.controller, self.task_manager)
        self.pages["Tasks"] = TasksPage(self.container, self.controller, self.task_manager)
        self.pages["Wheel"] = WheelPage(self.container, self.controller, self.task_manager)
        self.pages["Leaderboard"] = LeaderboardPage(self.container, self.controller)

    def create_nav_btn(self, text, page_name):
        # Using a Frame to hold the button helps with sizing
        btn = ctk.CTkButton(
            self.sidebar, 
            text=text, 
            command=lambda: self.show_page(page_name),
            fg_color="transparent", 
            text_color=TEXT_SECONDARY,
            hover_color="#1e293b",
            anchor="w",
            font=("Roboto Medium", 13),
            height=45,
            corner_radius=8,
            border_spacing=15 # Adds padding inside the button
        )
        btn.pack(fill="x", padx=15, pady=4)
        self.nav_buttons[page_name] = btn

    def show_page(self, page_name, animate=True):
        if self.current_page_name == page_name: return
        
        # Update Sidebar (The "Active Pill" Look)
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color=ACCENT_COLOR, text_color="white", hover_color="#4f46e5")
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY, hover_color="#1e293b")

        next_page = self.pages[page_name]
        if hasattr(next_page, "refresh"): next_page.refresh()
        elif hasattr(next_page, "refresh_data"): next_page.refresh_data()

        if not animate or not self.current_page_name:
            if self.current_page_name: self.pages[self.current_page_name].place_forget()
            next_page.place(x=0, y=0, relwidth=1, relheight=1)
            self.current_page_name = page_name
        else:
            old_page = self.pages[self.current_page_name]
            next_page.place(relx=1.0, y=0, relwidth=1, relheight=1)
            next_page.lift()
            self.animate_slide(old_page, next_page)
            self.current_page_name = page_name

    def animate_slide(self, old_page, new_page, step=0):
        limit = 12 # Slightly faster for snappy feel
        if step > limit:
            old_page.place_forget()
            new_page.place(relx=0, y=0, relwidth=1, relheight=1)
            return
        progress = step / limit
        ease = 1 - pow(1 - progress, 3)
        new_page.place(relx=1.0 - ease, y=0, relwidth=1, relheight=1)
        old_page.place(relx=0.0 - (ease * 0.15), y=0, relwidth=1, relheight=1)
        self.after(10, lambda: self.animate_slide(old_page, new_page, step + 1))