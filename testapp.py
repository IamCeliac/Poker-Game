import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import threading
import queue
import json
from server import SERVER_IP, SERVER_PORT


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Texas Hold'em Poker")
        self.geometry("460x680")
        self.configure(bg="#121212")
        self.resizable(False, False)

        # Player & Table State
        self.current_username = ""
        self.player_balance = 0
        self.open_tables = []          # List of dicts: [{"table_name": ..., "creator": ..., "min_bet": ...}]
        self.my_created_tables = set()

        self.current_table_name = ""
        self.current_table_creator = ""
        self.current_table_min_bet = 20
        self.table_players = []        # List of usernames currently seated
        self.last_game_state = None    # Latest "game_state" dict from server

        # Networking
        self.client_socket = None
        self.listener_running = False
        self.msg_queue = queue.Queue()

        # Theme configuration
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "bg": "#121212",
                "card_bg": "#1e1e1e",
                "fg": "#ffffff",
                "sub_fg": "#aaaaaa",
                "entry_bg": "#2c2c2c",
                "entry_fg": "#ffffff",
                "accent": "#007acc",
                "arena_bg": "#0b1612",
                "panel_bg": "#15221c",
                "toggle_text": "☀️ Light Mode"
            },
            "light": {
                "bg": "#f0f2f5",
                "card_bg": "#ffffff",
                "fg": "#1c1e21",
                "sub_fg": "#555555",
                "entry_bg": "#e4e6eb",
                "entry_fg": "#000000",
                "accent": "#005a9e",
                "arena_bg": "#1b3326",
                "panel_bg": "#234232",
                "toggle_text": "🌙 Dark Mode"
            }
        }

        self.container = tk.Frame(self, bg=self.themes["dark"]["bg"])
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for PageClass in (SignInPage, SignUpPage, UserPage, LoadTablesPage, GamePage):
            frame = PageClass(self.container, self)
            self.frames[PageClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(SignInPage)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(50, self.process_network_queue)

    def show_frame(self, page_class):
        if page_class == GamePage:
            self.geometry("1060x720")
        else:
            self.geometry("460x680")

        frame = self.frames[page_class]
        if hasattr(frame, "apply_theme"):
            frame.apply_theme()
        if hasattr(frame, "clear_inputs"):
            frame.clear_inputs()
        if page_class == LoadTablesPage:
            frame.refresh_tables()
        frame.tkraise()

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        for frame in self.frames.values():
            if hasattr(frame, "apply_theme"):
                frame.apply_theme()
        if LoadTablesPage in self.frames:
            self.frames[LoadTablesPage].refresh_tables()

    # --- NETWORKING & ASYNC DISPATCHER ---
    def start_network_listener(self, sock):
        self.client_socket = sock
        self.listener_running = True
        t = threading.Thread(target=self._socket_reader_loop, args=(sock,), daemon=True)
        t.start()

    def stop_network_listener(self):
        self.listener_running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

    def _socket_reader_loop(self, sock):
        buffer = ""
        while self.listener_running:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        parsed = json.loads(line)
                        self.msg_queue.put(parsed)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                break

    def send_action(self, payload_dict):
        if not self.client_socket:
            messagebox.showerror("Connection Error", "Not connected to the server.")
            return False
        try:
            data = (json.dumps(payload_dict) + "\n").encode("utf-8")
            self.client_socket.sendall(data)
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to send action: {e}")
            return False

    def sync_open_tables(self, raw_tables):
        cleaned = []
        self.my_created_tables.clear()
        for item in raw_tables:
            if isinstance(item, dict):
                t_name = item.get("table_name") or item.get("name", "")
                t_creator = item.get("creator") or item.get("owner", "")
                t_min_bet = int(item.get("min_bet", 20))
                if t_name:
                    cleaned.append({
                        "table_name": t_name,
                        "creator": t_creator,
                        "min_bet": t_min_bet
                    })
                    if t_creator == self.current_username:
                        self.my_created_tables.add(t_name)
            elif isinstance(item, str):
                cleaned.append({"table_name": item, "creator": "", "min_bet": 20})
        self.open_tables = cleaned

    def process_network_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get_nowait()
            if not isinstance(msg, dict):
                continue

            if msg.get("status") == "error":
                messagebox.showerror("Action Error", msg.get("message", "An error occurred."))
                continue

            msg_type = msg.get("type", "")

            # 1. User Settings Responses
            if msg_type == "change_username_success":
                self.current_username = msg.get("username", self.current_username)
                self.player_balance = msg.get("balance", self.player_balance)
                messagebox.showinfo("Success", f"Username updated to '{self.current_username}'!")
                self.frames[UserPage].clear_inputs()
                self.show_frame(LoadTablesPage)

            elif msg_type == "change_password_success":
                messagebox.showinfo("Success", "Password updated successfully!")
                self.frames[UserPage].clear_inputs()
                self.show_frame(LoadTablesPage)

            elif msg_type == "deleteuser_success":
                messagebox.showinfo("Account Deleted", "Your account has been deleted.")
                self.stop_network_listener()
                self.current_username = ""
                self.player_balance = 0
                self.show_frame(SignUpPage)

            # 2. Lobby & Balance Refill Responses
            elif msg_type in ("get_tables_list", "tables_list"):
                self.sync_open_tables(msg.get("open_tables", []))
                self.frames[LoadTablesPage].refresh_tables()

            elif msg_type == "refill_success":
                self.player_balance = msg.get("balance", 500)
                self.frames[LoadTablesPage].refresh_tables()
                messagebox.showinfo("Chips Refilled", msg.get("message", "Balance refilled to 500 chips!"))

            # 3. Table Creation / Join / Leave / Delete
            elif msg_type == "table_joined":
                t_name = msg.get("table_name", "")
                min_bet = int(msg.get("min_bet", 20))
                creator = msg.get("creator", self.current_username)
                self.current_table_name = t_name
                self.current_table_min_bet = min_bet
                self.current_table_creator = creator
                self.table_players = msg.get("players", [self.current_username])
                self.last_game_state = None
                self.my_created_tables.add(t_name)

                if not any(t["table_name"] == t_name for t in self.open_tables):
                    self.open_tables.append({
                        "table_name": t_name,
                        "creator": creator,
                        "min_bet": min_bet
                    })

                self.show_frame(GamePage)
                self.frames[GamePage].render_waiting_state(f"Table '{t_name}' created. Waiting for players...")

            elif msg_type == "player_joined":
                t_name = msg.get("table_name", "")
                self.current_table_name = t_name
                self.table_players = msg.get("players", [])

                # Look up creator and min_bet from known open_tables
                for t in self.open_tables:
                    if t["table_name"] == t_name:
                        self.current_table_creator = t.get("creator", "")
                        self.current_table_min_bet = t.get("min_bet", 20)
                        break

                self.show_frame(GamePage)
                if self.last_game_state is None or self.last_game_state.get("stage") == "Finished":
                    self.frames[GamePage].render_waiting_state(
                        f"Players seated ({len(self.table_players)}/5). Waiting for host to start..."
                    )

            elif msg_type == "player_left":
                self.table_players = msg.get("players", [])
                if self.last_game_state is None or self.last_game_state.get("stage") == "Finished":
                    self.frames[GamePage].render_waiting_state(
                        f"A player left the table. Seated: {', '.join(self.table_players)}"
                    )

            elif msg_type == "left_table":
                self.player_balance = msg.get("balance", self.player_balance)
                self.sync_open_tables(msg.get("open_tables", []))
                self.current_table_name = ""
                self.table_players = []
                self.last_game_state = None
                self.show_frame(LoadTablesPage)

            elif msg_type == "table_deleted":
                deleted_name = msg.get("table_name", "")
                self.open_tables = [t for t in self.open_tables if t["table_name"] != deleted_name]
                self.my_created_tables.discard(deleted_name)
                if self.current_table_name == deleted_name:
                    self.current_table_name = ""
                    self.table_players = []
                    self.last_game_state = None
                    self.show_frame(LoadTablesPage)
                else:
                    self.frames[LoadTablesPage].refresh_tables()
                messagebox.showinfo("Table Deleted", f"Table '{deleted_name}' was deleted.")

            # 4. Live Poker Game State Broadcast
            elif msg_type == "game_state":
                self.last_game_state = msg
                for p in msg.get("players", []):
                    if p.get("username") == self.current_username:
                        self.player_balance = p.get("balance", self.player_balance)
                self.table_players = [p.get("username") for p in msg.get("players", [])]
                self.frames[GamePage].update_from_game_state(msg)

        self.after(50, self.process_network_queue)

    def on_closing(self):
        self.stop_network_listener()
        self.destroy()


# =====================================================================
# SIGN IN PAGE
# =====================================================================
class SignInPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        self.theme_btn = tk.Button(
            top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=self.controller.toggle_theme
        )
        self.theme_btn.pack(side="left")

        self.logo_label = tk.Label(self, text="♠ ♥ ♣ ♦", font=("Segoe UI", 24, "bold"), fg="#e63946")
        self.logo_label.pack(pady=(25, 5))

        self.title_label = tk.Label(self, text="Texas Hold'em Portal", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(pady=(0, 25))

        self.lbl_user = tk.Label(self, text="Username", font=("Segoe UI", 10, "bold"))
        self.lbl_user.pack(anchor="w", padx=40)
        self.user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.user_entry.pack(fill="x", padx=40, pady=(4, 15), ipady=6)

        self.lbl_pass = tk.Label(self, text="Password", font=("Segoe UI", 10, "bold"))
        self.lbl_pass.pack(anchor="w", padx=40)
        self.pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.pass_entry.pack(fill="x", padx=40, pady=(4, 25), ipady=6)

        self.signin_btn = tk.Button(
            self, text="Sign In", font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white",
            bd=0, pady=10, cursor="hand2", command=self.SignOldUser
        )
        self.signin_btn.pack(fill="x", padx=40, pady=5)

        self.clear_btn = tk.Button(
            self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white",
            bd=0, pady=6, cursor="hand2", command=self.clear_inputs
        )
        self.clear_btn.pack(fill="x", padx=40, pady=(2, 12))

        self.switch_btn = tk.Button(
            self, text="Don't have an account? Sign Up", font=("Segoe UI", 9, "bold"),
            bd=0, fg="#007acc", cursor="hand2", command=lambda: controller.show_frame(SignUpPage)
        )
        self.switch_btn.pack(pady=10)

    def clear_inputs(self):
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        self.winfo_children()[0].configure(bg=t["bg"])
        self.logo_label.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_user.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_pass.configure(bg=t["bg"], fg=t["fg"])
        self.user_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.pass_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.switch_btn.configure(bg=t["bg"])

    def SignOldUser(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return

        payload = {"action": "signin", "username": username, "password": password}
        data = (json.dumps(payload) + "\n").encode("utf-8")

        try:
            self.controller.stop_network_listener()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            client_socket.sendall(data)
            server_response_raw = client_socket.recv(4096).decode("utf-8").strip()

            if not server_response_raw:
                client_socket.close()
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return

            first_line = server_response_raw.split("\n")[0]
            response = json.loads(first_line)

            if response.get("status") == "ok":
                self.controller.current_username = response.get("username", username)
                self.controller.player_balance = response.get("balance", 0)
                self.controller.sync_open_tables(response.get("open_tables", []))

                # Start persistent background listener for the rest of the session
                self.controller.start_network_listener(client_socket)
                self.clear_inputs()
                self.controller.show_frame(LoadTablesPage)
            else:
                client_socket.close()
                messagebox.showerror("Sign In Failed", response.get("message", "Signin failed."))

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")


# =====================================================================
# SIGN UP PAGE
# =====================================================================
class SignUpPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        self.theme_btn = tk.Button(
            top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=self.controller.toggle_theme
        )
        self.theme_btn.pack(side="left")

        self.logo_label = tk.Label(self, text="♠ ♥ ♣ ♦", font=("Segoe UI", 24, "bold"), fg="#28a745")
        self.logo_label.pack(pady=(25, 5))

        self.title_label = tk.Label(self, text="Create New Account", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(pady=(0, 25))

        self.lbl_user = tk.Label(self, text="Choose Username", font=("Segoe UI", 10, "bold"))
        self.lbl_user.pack(anchor="w", padx=40)
        self.user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.user_entry.pack(fill="x", padx=40, pady=(4, 15), ipady=6)

        self.lbl_pass = tk.Label(self, text="Choose Password", font=("Segoe UI", 10, "bold"))
        self.lbl_pass.pack(anchor="w", padx=40)
        self.pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.pass_entry.pack(fill="x", padx=40, pady=(4, 25), ipady=6)

        self.signup_btn = tk.Button(
            self, text="Create Account (500 Starting Chips)", font=("Segoe UI", 10, "bold"),
            bg="#28a745", fg="white", bd=0, pady=10, cursor="hand2", command=self.SignNewUser
        )
        self.signup_btn.pack(fill="x", padx=40, pady=5)

        self.clear_btn = tk.Button(
            self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white",
            bd=0, pady=6, cursor="hand2", command=self.clear_inputs
        )
        self.clear_btn.pack(fill="x", padx=40, pady=(2, 12))

        self.switch_btn = tk.Button(
            self, text="Already have an account? Sign In", font=("Segoe UI", 9, "bold"),
            bd=0, fg="#007acc", cursor="hand2", command=lambda: controller.show_frame(SignInPage)
        )
        self.switch_btn.pack(pady=10)

    def clear_inputs(self):
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        self.winfo_children()[0].configure(bg=t["bg"])
        self.logo_label.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_user.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_pass.configure(bg=t["bg"], fg=t["fg"])
        self.user_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.pass_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.switch_btn.configure(bg=t["bg"])

    def SignNewUser(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return

        payload = {"action": "signup", "username": username, "password": password}
        data = (json.dumps(payload) + "\n").encode("utf-8")

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            client_socket.sendall(data)
            server_response_raw = client_socket.recv(4096).decode("utf-8").strip()
            client_socket.close()

            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return

            response = json.loads(server_response_raw.split("\n")[0])
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "Account created with 500 chips! Please sign in.")
                self.clear_inputs()
                self.controller.show_frame(SignInPage)
            else:
                messagebox.showerror("Error", response.get("message", "Signup failed."))

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")


# =====================================================================
# USER SETTINGS PAGE
# =====================================================================
class UserPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)

        self.theme_btn = tk.Button(
            top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=self.controller.toggle_theme
        )
        self.theme_btn.pack(side="left")

        tk.Button(
            top_bar, text="Delete Account", font=("Segoe UI", 9, "bold"), bg="#dc3545", fg="white",
            bd=0, padx=10, pady=5, cursor="hand2", command=self.DeleteUser
        ).pack(side="right")

        self.title_label = tk.Label(self, text="Account Settings", font=("Segoe UI", 16, "bold"))
        self.title_label.pack(pady=(0, 10))

        # --- SECTION 1: CHANGE USERNAME ---
        self.lbl_uname_sec = tk.Label(self, text="Change Username", font=("Segoe UI", 11, "bold"))
        self.lbl_uname_sec.pack(anchor="w", padx=35, pady=(2, 2))

        self.lbl_curr_user = tk.Label(self, text="Current Username", font=("Segoe UI", 9))
        self.lbl_curr_user.pack(anchor="w", padx=35)
        self.curr_user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.curr_user_entry.pack(fill="x", padx=35, pady=(0, 6), ipady=3)

        self.lbl_new_user = tk.Label(self, text="New Username", font=("Segoe UI", 9))
        self.lbl_new_user.pack(anchor="w", padx=35)
        self.new_user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.new_user_entry.pack(fill="x", padx=35, pady=(0, 8), ipady=3)

        self.btn_up_user = tk.Button(
            self, text="Update Username", font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white",
            bd=0, pady=6, cursor="hand2", command=self.ChangeUsername
        )
        self.btn_up_user.pack(fill="x", padx=35, pady=(0, 14))

        # --- SECTION 2: CHANGE PASSWORD ---
        self.lbl_pass_sec = tk.Label(self, text="Change Password", font=("Segoe UI", 11, "bold"))
        self.lbl_pass_sec.pack(anchor="w", padx=35, pady=(0, 2))

        self.lbl_curr_pass = tk.Label(self, text="Current Password", font=("Segoe UI", 9))
        self.lbl_curr_pass.pack(anchor="w", padx=35)
        self.curr_pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.curr_pass_entry.pack(fill="x", padx=35, pady=(0, 6), ipady=3)

        self.lbl_new_pass1 = tk.Label(self, text="New Password", font=("Segoe UI", 9))
        self.lbl_new_pass1.pack(anchor="w", padx=35)
        self.new_pass_entry1 = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.new_pass_entry1.pack(fill="x", padx=35, pady=(0, 6), ipady=3)

        self.lbl_new_pass2 = tk.Label(self, text="Confirm New Password", font=("Segoe UI", 9))
        self.lbl_new_pass2.pack(anchor="w", padx=35)
        self.new_pass_entry2 = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.new_pass_entry2.pack(fill="x", padx=35, pady=(0, 8), ipady=3)

        self.btn_up_pass = tk.Button(
            self, text="Update Password", font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white",
            bd=0, pady=6, cursor="hand2", command=self.ChangePassword
        )
        self.btn_up_pass.pack(fill="x", padx=35, pady=(0, 12))

        self.clear_btn = tk.Button(
            self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white",
            bd=0, pady=5, cursor="hand2", command=self.clear_inputs
        )
        self.clear_btn.pack(fill="x", padx=35, pady=(0, 6))

        self.back_btn = tk.Button(
            self, text="← Back to Lobby", font=("Segoe UI", 9, "bold"), bd=0, pady=6,
            cursor="hand2", command=lambda: controller.show_frame(LoadTablesPage)
        )
        self.back_btn.pack(fill="x", padx=35)

    def clear_inputs(self):
        self.curr_user_entry.delete(0, tk.END)
        self.new_user_entry.delete(0, tk.END)
        self.curr_pass_entry.delete(0, tk.END)
        self.new_pass_entry1.delete(0, tk.END)
        self.new_pass_entry2.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=t["bg"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=t["bg"], fg=t["fg"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.lbl_uname_sec.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_pass_sec.configure(bg=t["bg"], fg=t["accent"])
        self.back_btn.configure(bg=t["card_bg"], fg=t["fg"])

    def ChangeUsername(self):
        current_username = self.curr_user_entry.get().strip()
        new_username = self.new_user_entry.get().strip()
        if not current_username or not new_username:
            messagebox.showerror("Error", "All username fields are required!")
            return
        self.controller.send_action({
            "action": "change_username",
            "current_username": current_username,
            "new_username": new_username
        })

    def ChangePassword(self):
        current_password = self.curr_pass_entry.get().strip()
        new_password = self.new_pass_entry1.get().strip()
        confirm_password = self.new_pass_entry2.get().strip()
        if not current_password or not new_password or not confirm_password:
            messagebox.showerror("Error", "All password fields are required!")
            return
        if new_password != confirm_password:
            messagebox.showerror("Error", "New passwords do not match!")
            return
        self.controller.send_action({
            "action": "change_password",
            "current_password": current_password,
            "new_password": new_password
        })

    def DeleteUser(self):
        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to permanently delete your account?"):
            return
        self.controller.send_action({
            "action": "delete_user",
            "username": self.controller.current_username
        })


# =====================================================================
# LOBBY / LOAD TABLES PAGE
# =====================================================================
class LoadTablesPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top Bar
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(fill="x", padx=25, pady=(15, 8))

        self.theme_btn = tk.Button(
            self.top_frame, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=self.controller.toggle_theme
        )
        self.theme_btn.pack(side="left")

        self.title_label = tk.Label(self.top_frame, text="Poker Lobby", font=("Segoe UI", 15, "bold"))
        self.title_label.pack(side="left", padx=12)

        self.settings_btn = tk.Button(
            self.top_frame, text="⚙ Settings", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=lambda: controller.show_frame(UserPage)
        )
        self.settings_btn.pack(side="right")

        # Player Info & Refill Banner
        self.profile_bar = tk.Frame(self, padx=12, pady=8)
        self.profile_bar.pack(fill="x", padx=25, pady=(0, 8))

        self.lbl_user_stats = tk.Label(self.profile_bar, text="Player: —  |  Chips: $0", font=("Segoe UI", 10, "bold"))
        self.lbl_user_stats.pack(side="left")

        self.refill_btn = tk.Button(
            self.profile_bar, text="💰 Refill to $500", font=("Segoe UI", 8, "bold"),
            bg="#f59e0b", fg="#111111", bd=0, padx=8, pady=3, cursor="hand2",
            command=self.RefillChips
        )
        self.refill_btn.pack(side="right", padx=(5, 0))

        self.refresh_btn = tk.Button(
            self.profile_bar, text="↻ Refresh", font=("Segoe UI", 8, "bold"),
            bg="#007acc", fg="white", bd=0, padx=8, pady=3, cursor="hand2",
            command=self.RequestTablesFromServer
        )
        self.refresh_btn.pack(side="right")

        # Scrollable Tables List
        self.container_frame = tk.Frame(self)
        self.container_frame.pack(fill="both", expand=True, padx=25, pady=5)

        self.canvas = tk.Canvas(self.container_frame, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create Table Section
        self.create_frame = tk.Frame(self)
        self.create_frame.pack(fill="x", padx=25, pady=15)

        self.lbl_create = tk.Label(self.create_frame, text="Create New Table", font=("Segoe UI", 11, "bold"))
        self.lbl_create.pack(anchor="w", pady=(0, 6))

        inputs_row = tk.Frame(self.create_frame)
        inputs_row.pack(fill="x", pady=(0, 8))
        self.inputs_row = inputs_row

        left_col = tk.Frame(inputs_row)
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.left_col = left_col
        self.lbl_tname = tk.Label(left_col, text="Table Name", font=("Segoe UI", 9))
        self.lbl_tname.pack(anchor="w")
        self.table_name_entry = tk.Entry(left_col, font=("Segoe UI", 11), bd=0, relief="flat")
        self.table_name_entry.pack(fill="x", ipady=4)

        right_col = tk.Frame(inputs_row)
        right_col.pack(side="right")
        self.right_col = right_col
        self.lbl_minbet = tk.Label(right_col, text="Min Bet (10-1000, even)", font=("Segoe UI", 9))
        self.lbl_minbet.pack(anchor="w")
        self.min_bet_entry = tk.Entry(right_col, font=("Segoe UI", 11), width=14, bd=0, relief="flat")
        self.min_bet_entry.insert(0, "20")
        self.min_bet_entry.pack(ipady=4)

        self.btn_create = tk.Button(
            self.create_frame, text="Create & Sit at Table", font=("Segoe UI", 10, "bold"),
            bg="#28a745", fg="white", bd=0, pady=8, cursor="hand2", command=self.CreateTable
        )
        self.btn_create.pack(fill="x", pady=(4, 5))

    def clear_inputs(self):
        self.table_name_entry.delete(0, tk.END)
        self.min_bet_entry.delete(0, tk.END)
        self.min_bet_entry.insert(0, "20")

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        self.top_frame.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.settings_btn.configure(bg=t["card_bg"], fg=t["fg"])

        self.profile_bar.configure(bg=t["card_bg"])
        self.lbl_user_stats.configure(bg=t["card_bg"], fg=t["fg"])

        self.container_frame.configure(bg=t["bg"])
        self.canvas.configure(bg=t["card_bg"])
        self.scrollable_frame.configure(bg=t["card_bg"])

        self.create_frame.configure(bg=t["bg"])
        self.inputs_row.configure(bg=t["bg"])
        self.left_col.configure(bg=t["bg"])
        self.right_col.configure(bg=t["bg"])
        self.lbl_create.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_tname.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_minbet.configure(bg=t["bg"], fg=t["fg"])
        self.table_name_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.min_bet_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])

    def RequestTablesFromServer(self):
        self.controller.send_action({"action": "get_tables"})

    def RefillChips(self):
        self.controller.send_action({"action": "refill_balance"})

    def refresh_tables(self):
        t = self.controller.themes[self.controller.current_theme]
        uname = self.controller.current_username or "Guest"
        bal = self.controller.player_balance
        self.lbl_user_stats.configure(text=f"👤 {uname}   |   🪙 Chips: ${bal}")

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tables = getattr(self.controller, "open_tables", [])
        if not tables:
            tk.Label(
                self.scrollable_frame,
                text="No open tables right now.\nCreate one below or click ↻ Refresh!",
                font=("Segoe UI", 10), fg="gray", bg=t["card_bg"], justify="center"
            ).pack(pady=40)
            return

        for item in tables:
            t_name = item.get("table_name", "")
            t_creator = item.get("creator", "Unknown")
            t_min_bet = int(item.get("min_bet", 20))
            sb = t_min_bet // 2
            req = t_min_bet * 2

            card = tk.Frame(self.scrollable_frame, bg=t["entry_bg"], padx=10, pady=8)
            card.pack(fill="x", padx=10, pady=5)

            info_col = tk.Frame(card, bg=t["entry_bg"])
            info_col.pack(side="left", fill="x", expand=True)

            tk.Label(
                info_col, text=f"🃏 {t_name}", font=("Segoe UI", 11, "bold"),
                fg=t["fg"], bg=t["entry_bg"], anchor="w"
            ).pack(fill="x")

            tk.Label(
                info_col,
                text=f"Host: {t_creator}  |  Blinds: ${sb}/${t_min_bet}  |  Min Buy-In: ${req}",
                font=("Segoe UI", 8), fg=t["sub_fg"], bg=t["entry_bg"], anchor="w"
            ).pack(fill="x")

            join_btn = tk.Button(
                card, text="Join", font=("Segoe UI", 9, "bold"), bg="#28a745", fg="white",
                bd=0, padx=12, pady=5, cursor="hand2",
                command=lambda n=t_name, c=t_creator, mb=t_min_bet: self.JoinTable(n, c, mb)
            )
            join_btn.pack(side="right", padx=4)

            if t_creator == self.controller.current_username or t_name in self.controller.my_created_tables:
                del_btn = tk.Button(
                    card, text="Delete", font=("Segoe UI", 9, "bold"), bg="#dc3545", fg="white",
                    bd=0, padx=10, pady=5, cursor="hand2",
                    command=lambda n=t_name: self.DeleteTable(n)
                )
                del_btn.pack(side="right", padx=4)

    def CreateTable(self):
        new_table_name = self.table_name_entry.get().strip()
        min_bet_raw = self.min_bet_entry.get().strip()

        if not new_table_name:
            messagebox.showerror("Error", "Table name cannot be empty.")
            return

        try:
            min_bet = int(min_bet_raw)
        except ValueError:
            messagebox.showerror("Error", "Minimum bet must be a valid integer.")
            return

        if min_bet < 10 or min_bet > 1000 or min_bet % 2 != 0:
            messagebox.showerror("Error", "Minimum bet must be an even number between 10 and 1000.")
            return

        self.controller.send_action({
            "action": "create_table",
            "table_name": new_table_name,
            "min_bet": min_bet
        })

    def JoinTable(self, selected_table_name, creator="", min_bet=20):
        self.controller.current_table_creator = creator
        self.controller.current_table_min_bet = min_bet
        self.controller.send_action({
            "action": "join_table",
            "table_name": selected_table_name
        })

    def DeleteTable(self, selected_table_name):
        if not messagebox.askyesno("Confirm Delete", f"Delete table '{selected_table_name}'?"):
            return
        self.controller.send_action({
            "action": "delete_table",
            "table_name": selected_table_name
        })


# =====================================================================
# GAME PAGE (VISUAL POKER TABLE & PHYSICAL CARDS)
# =====================================================================
class GamePage(tk.Frame):
    SUIT_SYMBOLS = {
        "Hearts": ("♥", "#d92027"),
        "Diamonds": ("♦", "#d92027"),
        "Spades": ("♠", "#1a1a2e"),
        "Clubs": ("♣", "#1a1a2e")
    }
    RANK_SHORT = {
        "Ace": "A",
        "King": "K",
        "Queen": "Q",
        "Jack": "J"
    }

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- 1. TOP HEADER BAR ---
        self.top_bar = tk.Frame(self, pady=8, padx=18)
        self.top_bar.pack(fill="x")

        self.theme_btn = tk.Button(
            self.top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5,
            cursor="hand2", command=self.controller.toggle_theme
        )
        self.theme_btn.pack(side="left")

        self.lbl_table_info = tk.Label(
            self.top_bar, text="Table: —", font=("Segoe UI", 12, "bold")
        )
        self.lbl_table_info.pack(side="left", padx=18)

        self.leave_btn = tk.Button(
            self.top_bar, text="🚪 Leave Table", font=("Segoe UI", 9, "bold"),
            bg="#dc3545", fg="white", bd=0, padx=14, pady=6, cursor="hand2",
            command=self.LeaveTable
        )
        self.leave_btn.pack(side="right", padx=(6, 0))

        self.delete_table_btn = tk.Button(
            self.top_bar, text="🗑 Delete Table", font=("Segoe UI", 9, "bold"),
            bg="#7f1d1d", fg="white", bd=0, padx=12, pady=6, cursor="hand2",
            command=self.DeleteCurrentTable
        )
        self.delete_table_btn.pack(side="right", padx=6)

        self.start_round_btn = tk.Button(
            self.top_bar, text="▶ Start Hand", font=("Segoe UI", 10, "bold"),
            bg="#f59e0b", fg="#111111", bd=0, padx=16, pady=6, cursor="hand2",
            command=self.StartRound
        )
        self.start_round_btn.pack(side="right", padx=6)

        # --- 2. POKER TABLE CANVAS ---
        self.table_canvas = tk.Canvas(self, width=1020, height=530, highlightthickness=0)
        self.table_canvas.pack(fill="both", expand=True, padx=15, pady=4)

        # --- 3. BOTTOM ACTION BAR ---
        self.action_bar = tk.Frame(self, pady=10, padx=18)
        self.action_bar.pack(fill="x", side="bottom")

        self.lbl_turn_indicator = tk.Label(
            self.action_bar, text="Waiting for hand to start...",
            font=("Segoe UI", 10, "bold"), fg="#fbbf24"
        )
        self.lbl_turn_indicator.pack(side="left", padx=(0, 15))

        # Action Buttons
        btn_frame = tk.Frame(self.action_bar)
        btn_frame.pack(side="right")
        self.btn_frame = btn_frame

        self.btn_fold = tk.Button(
            btn_frame, text="Fold", font=("Segoe UI", 10, "bold"), bg="#dc2626", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("fold")
        )
        self.btn_fold.pack(side="left", padx=4)

        self.btn_check = tk.Button(
            btn_frame, text="Check", font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("check")
        )
        self.btn_check.pack(side="left", padx=4)

        self.btn_call = tk.Button(
            btn_frame, text="Call", font=("Segoe UI", 10, "bold"), bg="#0d9488", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("call")
        )
        self.btn_call.pack(side="left", padx=4)

        # Bet / Raise amount entry + quick chips
        bet_box = tk.Frame(btn_frame)
        bet_box.pack(side="left", padx=10)
        self.bet_box = bet_box

        self.amount_entry = tk.Entry(
            bet_box, font=("Segoe UI", 11, "bold"), width=7, justify="center", bd=0
        )
        self.amount_entry.insert(0, "40")
        self.amount_entry.pack(side="left", ipady=6, padx=(0, 4))

        for chip_val in (10, 20, 50, 100):
            b = tk.Button(
                bet_box, text=f"+{chip_val}", font=("Segoe UI", 8, "bold"),
                bg="#374151", fg="white", bd=0, padx=6, pady=6, cursor="hand2",
                command=lambda v=chip_val: self.AddChipToEntry(v)
            )
            b.pack(side="left", padx=1)

        self.btn_bet = tk.Button(
            btn_frame, text="Bet", font=("Segoe UI", 10, "bold"), bg="#16a34a", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("bet")
        )
        self.btn_bet.pack(side="left", padx=4)

        self.btn_raise = tk.Button(
            btn_frame, text="Raise To", font=("Segoe UI", 10, "bold"), bg="#7c3aed", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("raise")
        )
        self.btn_raise.pack(side="left", padx=4)

        self.btn_allin = tk.Button(
            btn_frame, text="🔥 All-In", font=("Segoe UI", 10, "bold"), bg="#d97706", fg="white",
            bd=0, padx=14, pady=7, cursor="hand2", command=lambda: self.SendMove("all_in")
        )
        self.btn_allin.pack(side="left", padx=4)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["arena_bg"])
        self.top_bar.configure(bg=t["panel_bg"])
        self.lbl_table_info.configure(bg=t["panel_bg"], fg="#ffffff")
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.table_canvas.configure(bg=t["arena_bg"])
        self.action_bar.configure(bg=t["panel_bg"])
        self.lbl_turn_indicator.configure(bg=t["panel_bg"])
        self.btn_frame.configure(bg=t["panel_bg"])
        self.bet_box.configure(bg=t["panel_bg"])
        self.amount_entry.configure(bg="#ffffff", fg="#111111")

        if self.controller.last_game_state:
            self.update_from_game_state(self.controller.last_game_state)
        else:
            self.render_waiting_state("Waiting for host to start the hand...")

    def AddChipToEntry(self, val):
        try:
            curr = int(self.amount_entry.get().strip())
        except ValueError:
            curr = 0
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, str(curr + val))

    def StartRound(self):
        self.controller.send_action({"action": "start_round"})

    def LeaveTable(self):
        self.controller.send_action({"action": "leave_table"})

    def DeleteCurrentTable(self):
        t_name = self.controller.current_table_name
        if not t_name:
            return
        if messagebox.askyesno("Delete Table", f"Delete table '{t_name}' and return to lobby?"):
            self.controller.send_action({"action": "delete_table", "table_name": t_name})

    def SendMove(self, move_type):
        amount = 0
        if move_type in ("bet", "raise"):
            try:
                amount = int(self.amount_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Amount", "Enter a valid chip amount for Bet/Raise.")
                return
        self.controller.send_action({
            "action": "game_move",
            "move": move_type,
            "amount": amount
        })

    def set_action_buttons_state(self, is_my_turn, current_bet=0):
        state = "normal" if is_my_turn else "disabled"
        self.btn_fold.configure(state=state)
        self.btn_check.configure(state=state)
        self.btn_call.configure(state=state)
        self.btn_allin.configure(state=state)
        if is_my_turn:
            self.btn_bet.configure(state="normal" if current_bet == 0 else "disabled")
            self.btn_raise.configure(state="normal" if current_bet > 0 else "disabled")
        else:
            self.btn_bet.configure(state="disabled")
            self.btn_raise.configure(state="disabled")

    def update_header_controls(self, stage_name="Waiting"):
        t_name = self.controller.current_table_name or "Table"
        mb = self.controller.current_table_min_bet
        creator = self.controller.current_table_creator or "Host"
        self.lbl_table_info.configure(
            text=f"🃏 {t_name}   |   Blinds: ${mb // 2}/${mb}   |   Host: {creator}   |   Stage: {stage_name}"
        )

        is_host = (creator == self.controller.current_username) or (t_name in self.controller.my_created_tables)
        can_start = is_host and stage_name in ("Waiting", "Finished")
        self.start_round_btn.configure(state="normal" if can_start else "disabled")
        self.delete_table_btn.configure(state="normal" if is_host else "disabled")

    # --- CANVAS RENDERING FOR PHYSICAL TABLE & CARDS ---
    def draw_poker_table_base(self, pot=0, current_bet=0, stage="Waiting", banner_text="", winner_text=None):
        c = self.table_canvas
        c.delete("all")

        # 1. Outer Wood Rail & Inner Felt Oval
        c.create_oval(90, 45, 930, 475, fill="#4a2511", outline="#2b1408", width=6)
        c.create_oval(108, 60, 912, 460, fill="#1c1c1c", outline="#6b381d", width=3)
        c.create_oval(124, 74, 896, 446, fill="#0f5c2e", outline="#1e7a44", width=3)
        c.create_oval(155, 102, 865, 418, fill="", outline="#27854d", width=2, dash=(6, 4))

        # 2. Pot & Current Bet Badge
        c.create_rectangle(390, 118, 630, 166, fill="#09351b", outline="#fbbf24", width=2)
        c.create_text(
            510, 134, text=f"🪙 TOTAL POT: ${pot}",
            fill="#fbbf24", font=("Segoe UI", 12, "bold")
        )
        c.create_text(
            510, 153, text=f"Current Street Bet: ${current_bet}   •   Stage: {stage.upper()}",
            fill="#d1fae5", font=("Segoe UI", 9, "bold")
        )

        # 3. Last Action / Status Banner
        if winner_text:
            c.create_rectangle(230, 322, 790, 358, fill="#78350f", outline="#fbbf24", width=2)
            c.create_text(
                510, 340, text=f"🏆 {winner_text}",
                fill="#fef08a", font=("Segoe UI", 10, "bold")
            )
        elif banner_text:
            c.create_rectangle(260, 324, 760, 354, fill="#082f17", outline="#1e7a44", width=1)
            c.create_text(
                510, 339, text=banner_text,
                fill="#a7f3d0", font=("Segoe UI", 9, "bold")
            )

    def draw_physical_card(self, x, y, card_str, width=62, height=88):
        """Draws a physical playing card (face-up or patterned card-back) at top-left (x, y)."""
        c = self.table_canvas
        # Drop shadow
        c.create_rectangle(x + 3, y + 3, x + width + 3, y + height + 3, fill="#062311", outline="")

        if card_str == "Hidden" or not card_str:
            # Casino Card Back
            c.create_rectangle(x, y, x + width, y + height, fill="#ffffff", outline="#d1d5db", width=2)
            c.create_rectangle(x + 4, y + 4, x + width - 4, y + height - 4, fill="#991b1b", outline="#fca5a5", width=1)
            c.create_oval(
                x + width * 0.28, y + height * 0.28,
                x + width * 0.72, y + height * 0.72,
                fill="#7f1d1d", outline="#fde047", width=1
            )
            c.create_text(x + width / 2, y + height / 2, text="♠", fill="#fde047", font=("Segoe UI", 12, "bold"))
            return

        # Parse "<Rank> of <Suit>"
        parts = card_str.split(" of ")
        raw_rank = parts[0] if len(parts) > 0 else "?"
        raw_suit = parts[1] if len(parts) > 1 else "Spades"

        rank_txt = self.RANK_SHORT.get(raw_rank, str(raw_rank))
        suit_sym, suit_color = self.SUIT_SYMBOLS.get(raw_suit, ("♠", "#1a1a2e"))

        # White Card Face
        c.create_rectangle(x, y, x + width, y + height, fill="#ffffff", outline="#9ca3af", width=2)

        # Top-Left Index
        c.create_text(x + 11, y + 12, text=rank_txt, fill=suit_color, font=("Segoe UI", 10, "bold"))
        c.create_text(x + 11, y + 25, text=suit_sym, fill=suit_color, font=("Segoe UI", 9, "bold"))

        # Center Giant Pip
        c.create_text(x + width / 2, y + height / 2, text=suit_sym, fill=suit_color, font=("Segoe UI", 22, "bold"))

        # Bottom-Right Index
        c.create_text(x + width - 11, y + height - 12, text=rank_txt, fill=suit_color, font=("Segoe UI", 9, "bold"))

    def draw_community_cards(self, community_cards):
        c = self.table_canvas
        start_x = 328
        y = 195
        spacing = 74
        for i in range(5):
            slot_x = start_x + i * spacing
            if i < len(community_cards):
                self.draw_physical_card(slot_x, y, community_cards[i], width=62, height=88)
            else:
                # Empty community slot outline on felt
                c.create_rectangle(
                    slot_x, y, slot_x + 62, y + 88,
                    fill="#0b4622", outline="#28804a", width=2, dash=(4, 4)
                )

    def draw_player_seats(self, players_list):
        """
        Positions up to 5 players around the table, rotating the list so the
        logged-in user is ALWAYS at Seat 0 (Bottom Center Hero Seat).
        """
        c = self.table_canvas
        seat_coords = [
            (510, 455, True),    # Seat 0: Bottom Center (Hero)
            (145, 375, False),   # Seat 1: Bottom Left
            (165, 115, False),   # Seat 2: Top Left
            (855, 115, False),   # Seat 3: Top Right
            (875, 375, False),   # Seat 4: Bottom Right
        ]

        # Rotate players_list so current_username is index 0
        rotated = list(players_list)
        my_idx = next(
            (i for i, p in enumerate(rotated) if p.get("username") == self.controller.current_username),
            0
        )
        if rotated:
            rotated = rotated[my_idx:] + rotated[:my_idx]

        for seat_idx, (sx, sy, is_hero) in enumerate(seat_coords):
            if seat_idx >= len(rotated):
                # Draw Open Seat Placeholder
                c.create_oval(sx - 45, sy - 18, sx + 45, sy + 18, fill="#0b2916", outline="#1e5635", width=1)
                c.create_text(sx, sy, text="Open Seat", fill="#4b7bec", font=("Segoe UI", 8))
                continue

            p = rotated[seat_idx]
            uname = p.get("username", "Player")
            bal = p.get("balance", 0)
            is_folded = p.get("is_folded", False)
            is_turn = p.get("is_turn", False)
            hand = p.get("hand", [])

            # Draw Player's 2 Hole Cards above their seat box
            if hand:
                cw = 60 if is_hero else 50
                ch = 84 if is_hero else 70
                card_y = sy - ch - 28
                self.draw_physical_card(sx - cw - 3, card_y, hand[0], width=cw, height=ch)
                if len(hand) > 1:
                    self.draw_physical_card(sx + 3, card_y, hand[1], width=cw, height=ch)

            # Seat Plate Styling
            if is_turn:
                box_bg = "#1e293b"
                border_col = "#fbbf24"
                border_w = 3
                status_tag = "⚡ THINKING..."
                tag_col = "#fbbf24"
            elif is_folded:
                box_bg = "#27272a"
                border_col = "#ef4444"
                border_w = 2
                status_tag = "FOLDED"
                tag_col = "#f87171"
            else:
                box_bg = "#111827"
                border_col = "#10b981" if is_hero else "#6b7280"
                border_w = 2
                status_tag = "YOU" if is_hero else "ACTIVE"
                tag_col = "#34d399" if is_hero else "#9ca3af"

            c.create_rectangle(
                sx - 85, sy - 26, sx + 85, sy + 26,
                fill=box_bg, outline=border_col, width=border_w
            )
            c.create_text(
                sx, sy - 11, text=f"{uname} ({status_tag})",
                fill=tag_col, font=("Segoe UI", 9, "bold")
            )
            c.create_text(
                sx, sy + 9, text=f"🪙 ${bal}",
                fill="#ffffff", font=("Segoe UI", 10, "bold")
            )

    def render_waiting_state(self, message="Waiting for players..."):
        self.update_header_controls(stage_name="Waiting")
        self.set_action_buttons_state(False)
        self.lbl_turn_indicator.configure(text=message, fg="#fbbf24")

        self.draw_poker_table_base(pot=0, current_bet=0, stage="Lobby", banner_text=message)
        self.draw_community_cards([])

        seated_dicts = [
            {
                "username": u,
                "balance": self.controller.player_balance if u == self.controller.current_username else "—",
                "is_folded": False,
                "is_turn": False,
                "hand": []
            }
            for u in self.controller.table_players
        ]
        self.draw_player_seats(seated_dicts)

    def update_from_game_state(self, state):
        stage = state.get("stage", "Pre-Flop")
        pot = state.get("pot", 0)
        current_bet = state.get("current_bet", 0)
        current_turn = state.get("current_turn")
        community_cards = state.get("community_cards", [])
        players = state.get("players", [])
        last_action = state.get("last_action", "")
        winner_message = state.get("winner_message")

        self.update_header_controls(stage_name=stage)

        is_my_turn = (current_turn == self.controller.current_username) and (stage != "Finished")
        self.set_action_buttons_state(is_my_turn, current_bet=current_bet)

        if stage == "Finished":
            turn_text = winner_message or last_action or "Hand Finished! Host can start the next hand."
            self.lbl_turn_indicator.configure(text=turn_text, fg="#4ade80")
        elif is_my_turn:
            self.lbl_turn_indicator.configure(
                text=f"⚡ YOUR TURN! (Table Bet: ${current_bet}  |  Your Chips: ${self.controller.player_balance})",
                fg="#fbbf24"
            )
        else:
            self.lbl_turn_indicator.configure(
                text=f"Waiting for {current_turn} to act...  ({last_action})",
                fg="#93c5fd"
            )

        self.draw_poker_table_base(
            pot=pot,
            current_bet=current_bet,
            stage=stage,
            banner_text=last_action,
            winner_text=winner_message
        )
        self.draw_community_cards(community_cards)
        self.draw_player_seats(players)


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()