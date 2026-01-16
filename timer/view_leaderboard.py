import customtkinter as ctk
import requests
import threading
import config

class LeaderboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Global Leaderboard", font=("Roboto Medium", 20)).pack(pady=20)
        self.lb_scroll = ctk.CTkScrollableFrame(self, width=350, height=350)
        self.lb_scroll.pack(fill="both", expand=True, padx=20, pady=20)

    def refresh_data(self):
        for widget in self.lb_scroll.winfo_children():
            widget.destroy()
            
        loading = ctk.CTkLabel(self.lb_scroll, text="Calculating scores...")
        loading.pack(pady=20)

        threading.Thread(target=self.fetch_and_aggregate, args=(loading,)).start()

    def fetch_and_aggregate(self, loading_label):
        try:
            resp = requests.get(config.FIREBASE_URL).json()
            self.after(0, lambda: loading_label.destroy())

            if not resp:
                self.after(0, lambda: ctk.CTkLabel(self.lb_scroll, text="No data yet.").pack())
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
                
                card_color = ("gray85", "gray20")
                text_color = "white"
                if rank == 1: text_color = "#FFD700" 
                elif rank == 2: text_color = "#C0C0C0" 
                elif rank == 3: text_color = "#CD7F32" 
                
                self.after(0, lambda n=name, t=time_str, tc=total_tasks, h=history, r=rank, c=card_color, txt=text_color: 
                           self.create_row(n, t, tc, h, r, c, txt))
                rank += 1
        except Exception as e:
            print(f"LB Error: {e}")

    def create_row(self, name, time_str, task_count, history, rank, bg_color, text_color):
        card = ctk.CTkFrame(self.lb_scroll, fg_color=bg_color)
        card.pack(fill="x", pady=5, padx=5)
        
        def on_click(event): self.show_user_details(name, time_str, task_count, history)
        card.bind("<Button-1>", on_click)

        # Labels
        l1 = ctk.CTkLabel(card, text=f"#{rank}", font=("Roboto Medium", 14), width=30, text_color=text_color)
        l1.pack(side="left", padx=10)
        l2 = ctk.CTkLabel(card, text=name, font=("Roboto Medium", 14), text_color=text_color)
        l2.pack(side="left", padx=5)
        l3 = ctk.CTkLabel(card, text=time_str, font=("Roboto", 14), text_color="gray70")
        l3.pack(side="right", padx=15)
        
        # Bind events for labels too
        for w in card.winfo_children(): w.bind("<Button-1>", on_click)

    def show_user_details(self, name, time_str, task_count, history):
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"{name}'s Profile")
        detail_window.geometry("300x450")
        detail_window.attributes('-topmost', True)
        detail_window.lift()
        
        # Header Name
        ctk.CTkLabel(detail_window, text=name, font=("Roboto Medium", 24)).pack(pady=(20, 5))
        ctk.CTkLabel(detail_window, text="Focus Stats", text_color="gray").pack(pady=(0, 20))

        # 🟢 NEW: Stats Grid (Restored)
        stats_frame = ctk.CTkFrame(detail_window, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20)
        
        # Time Card
        f1 = ctk.CTkFrame(stats_frame, fg_color=("gray90", "gray20"))
        f1.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(f1, text="Time", font=("Arial", 12)).pack(pady=(5,0))
        ctk.CTkLabel(f1, text=time_str, font=("Arial", 16, "bold"), text_color="#00C853").pack(pady=(0,5))

        # Tasks Card
        f2 = ctk.CTkFrame(stats_frame, fg_color=("gray90", "gray20"))
        f2.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(f2, text="Tasks Done", font=("Arial", 12)).pack(pady=(5,0))
        ctk.CTkLabel(f2, text=str(task_count), font=("Arial", 16, "bold"), text_color="#1E88E5").pack(pady=(0,5))

        # Task History List
        ctk.CTkLabel(detail_window, text="Completed Tasks", font=("Roboto Medium", 14)).pack(pady=(30, 10))
        
        scroll = ctk.CTkScrollableFrame(detail_window, width=250, height=150)
        scroll.pack()

        if not history:
            ctk.CTkLabel(scroll, text="No tasks recorded.", text_color="gray").pack(pady=20)
        else:
            for task_name, count in history.items():
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                display_text = f"✅ {task_name}"
                if count > 1:
                    display_text += f" (x{count})"
                    
                ctk.CTkLabel(row, text=display_text, anchor="w", font=("Roboto", 12)).pack(fill="x", padx=5)