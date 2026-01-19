import customtkinter as ctk
import requests
import threading
import config

BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
ACCENT_COLOR = "#6366f1"
TEXT_SEC = "#94a3b8"

class LeaderboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.header = ctk.CTkLabel(self, text="GLOBAL RANKINGS", font=("Roboto Medium", 14), text_color=TEXT_SEC)
        self.header.pack(pady=(40, 20))

        self.lb_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lb_scroll.pack(fill="both", expand=True, padx=60, pady=20)

    def refresh(self):
        for widget in self.lb_scroll.winfo_children(): widget.destroy()
            
        loading = ctk.CTkLabel(self.lb_scroll, text="Fetching Data...", font=("Roboto", 14), text_color=TEXT_SEC)
        loading.pack(pady=50)

        threading.Thread(target=self.fetch_and_aggregate, args=(loading,)).start()

    def fetch_and_aggregate(self, loading_label):
        try:
            resp = requests.get(config.FIREBASE_URL).json()
            self.after(0, lambda: loading_label.destroy())

            if not resp:
                self.after(0, lambda: ctk.CTkLabel(self.lb_scroll, text="No data found.", font=("Roboto", 16), text_color=TEXT_SEC).pack(pady=50))
                return

            user_stats = {}
            for entry in resp.values():
                name = entry.get("username", "Unknown")
                duration_str = entry.get("duration", "0 min")
                session_tasks = entry.get("tasks_done", []) 
                session_task_count = entry.get("task_count", 0) 
                
                try: minutes = int(str(duration_str).split()[0])
                except: minutes = 0
                
                if name not in user_stats:
                    user_stats[name] = {'minutes': 0, 'tasks': 0, 'history': {}}
                
                user_stats[name]['minutes'] += minutes
                user_stats[name]['tasks'] += session_task_count
                for t in session_tasks:
                    current_count = user_stats[name]['history'].get(t, 0)
                    user_stats[name]['history'][t] = current_count + 1

            sorted_users = sorted(user_stats.items(), key=lambda item: item[1]['minutes'], reverse=True)

            rank = 1
            for name, stats in sorted_users:
                total_mins = stats['minutes']
                total_tasks = stats['tasks']
                history = stats['history']
                hours, mins = divmod(total_mins, 60)
                time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                
                # Colors
                bg_color = CARD_COLOR
                rank_color = TEXT_SEC
                
                if rank == 1: 
                    rank_color = "#fcd34d" # Gold
                    bg_color = "#422006"   # Dark Brown/Gold tint
                elif rank == 2: rank_color = "#e2e8f0" # Silver
                elif rank == 3: rank_color = "#fdba74" # Bronze
                
                self.after(0, lambda n=name, t=time_str, tc=total_tasks, h=history, r=rank, bg=bg_color, rc=rank_color: 
                           self.create_row(n, t, tc, h, r, bg, rc))
                rank += 1
        except Exception as e:
            print(f"LB Error: {e}")

    def create_row(self, name, time_str, total_tasks, history, rank, bg_color, rank_color):
        # Card with subtle border
        card = ctk.CTkFrame(self.lb_scroll, fg_color=bg_color, corner_radius=10, height=60, border_width=1, border_color="#334155")
        card.pack(fill="x", pady=6)
        
        def on_click(event): self.show_user_details(name, time_str, total_tasks, history)
        card.bind("<Button-1>", on_click)

        ctk.CTkLabel(card, text=f"#{rank}", font=("Roboto", 16, "bold"), width=50, text_color=rank_color).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(card, text=name, font=("Roboto Medium", 15), text_color="white").pack(side="left", padx=10)
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="right", padx=25)
        ctk.CTkLabel(info, text=time_str, font=("Roboto", 16, "bold"), text_color=ACCENT_COLOR).pack(anchor="e")
        ctk.CTkLabel(info, text=f"{total_tasks} Tasks", font=("Roboto", 11), text_color=TEXT_SEC).pack(anchor="e")
        
        for w in card.winfo_children(): w.bind("<Button-1>", on_click)

    def show_user_details(self, name, time_str, total_tasks, history):
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(name)
        detail_window.geometry("350x550")
        detail_window.attributes('-topmost', True)
        
        bg = ctk.CTkFrame(detail_window, fg_color=BG_COLOR)
        bg.pack(fill="both", expand=True)

        ctk.CTkLabel(bg, text=name.upper(), font=("Roboto", 24, "bold"), text_color="white").pack(pady=(40, 20))

        # Stats Grid
        stats_frame = ctk.CTkFrame(bg, fg_color="transparent")
        stats_frame.pack(pady=10)

        t_col = ctk.CTkFrame(stats_frame, fg_color="transparent")
        t_col.pack(side="left", padx=25)
        ctk.CTkLabel(t_col, text="TIME FOCUSED", font=("Roboto Medium", 10), text_color=TEXT_SEC).pack()
        ctk.CTkLabel(t_col, text=time_str, font=("Roboto Mono", 24, "bold"), text_color=ACCENT_COLOR).pack()

        c_col = ctk.CTkFrame(stats_frame, fg_color="transparent")
        c_col.pack(side="left", padx=25)
        ctk.CTkLabel(c_col, text="TOTAL TASKS", font=("Roboto Medium", 10), text_color=TEXT_SEC).pack()
        ctk.CTkLabel(c_col, text=str(total_tasks), font=("Roboto Mono", 24, "bold"), text_color="#10b981").pack()

        ctk.CTkLabel(bg, text="HISTORY", font=("Roboto Medium", 12), text_color=TEXT_SEC).pack(pady=(30, 10))
        
        scroll = ctk.CTkScrollableFrame(bg, width=280, height=200, fg_color=CARD_COLOR, corner_radius=12)
        scroll.pack()

        if not history:
            ctk.CTkLabel(scroll, text="No tasks recorded.", text_color="gray", font=("Roboto", 12)).pack(pady=20)
        else:
            for task_name, count in history.items():
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                txt = f"{task_name}"
                if count > 1: txt += f" (x{count})"
                ctk.CTkLabel(row, text=txt, font=("Roboto", 13), text_color="#e2e8f0").pack(anchor="w", padx=10)