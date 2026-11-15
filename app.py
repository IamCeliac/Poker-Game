import tkinter as tk
from tkinter import messagebox, simpledialog
import socket 
import json
from server import SERVER_IP, SERVER_PORT

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Poker Game - Portal")
        self.geometry("400x600")
        self.configure(bg="#121212")
        self.resizable(False, False)
        
        self.current_username = ""
        self.player_balance = 0
        self.open_tables = []
        self.my_created_tables = set()  
        
        # Theme configuration: "dark" or "light"
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "bg": "#121212",
                "card_bg": "#1e1e1e",
                "fg": "#ffffff",
                "entry_bg": "#2c2c2c",
                "entry_fg": "#ffffff",
                "accent": "#007acc",
                "toggle_text": "☀️ Light Mode"
            },
            "light": {
                "bg": "#f5f5f5",
                "card_bg": "#ffffff",
                "fg": "#222222",
                "entry_bg": "#e8e8e8",
                "entry_fg": "#000000",
                "accent": "#005a9e",
                "toggle_text": "🌙 Dark Mode"
            }
        }
        
        container = tk.Frame(self, bg=self.themes["dark"]["bg"])
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.client_socket = None
        
        self.frames = {}
        
        for PageClass in (SignInPage, SignUpPage, UserPage, LoadTablesPage, GamePage):
            frame = PageClass(container, self)
            self.frames[PageClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame(SignInPage)
            
    def show_frame(self, page_class):
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
        
class UserPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  
        
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        
        self.theme_btn = tk.Button(top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=self.controller.toggle_theme)
        self.theme_btn.pack(side="left")
        
        tk.Button(top_bar, text="Delete Account", font=("Segoe UI", 9, "bold"), bg="#dc3545", fg="white", bd=0, padx=10, pady=5, cursor="hand2",
                  command=self.DeleteUser).pack(side="right")
        
        self.title_label = tk.Label(self, text="User Settings", font=("Segoe UI", 16, "bold"))
        self.title_label.pack(pady=(0, 5))
        
        # --- SECTION 1: CHANGE USERNAME ---
        self.lbl_uname_sec = tk.Label(self, text="Change Username", font=("Segoe UI", 11, "bold"))
        self.lbl_uname_sec.pack(anchor="w", padx=35, pady=(2, 2))
        
        self.lbl_curr_user = tk.Label(self, text="Current Username", font=("Segoe UI", 9))
        self.lbl_curr_user.pack(anchor="w", padx=35)
        self.curr_user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.curr_user_entry.pack(fill="x", padx=35, pady=(0, 6), ipady=2)
        
        self.lbl_new_user = tk.Label(self, text="New Username", font=("Segoe UI", 9))
        self.lbl_new_user.pack(anchor="w", padx=35)
        self.new_user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.new_user_entry.pack(fill="x", padx=35, pady=(0, 8), ipady=2)
        
        self.btn_up_user = tk.Button(self, text="Update Username", font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white", bd=0, pady=5, cursor="hand2",
                  command=self.ChangeUsername)
        self.btn_up_user.pack(fill="x", padx=35, pady=(0, 10))
        
        # --- SECTION 2: CHANGE PASSWORD ---
        self.lbl_pass_sec = tk.Label(self, text="Change Password", font=("Segoe UI", 11, "bold"))
        self.lbl_pass_sec.pack(anchor="w", padx=35, pady=(0, 2))
        
        self.lbl_curr_pass = tk.Label(self, text="Current Password", font=("Segoe UI", 9))
        self.lbl_curr_pass.pack(anchor="w", padx=35)
        self.curr_pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.curr_pass_entry.pack(fill="x", padx=35, pady=(0, 6), ipady=2)
        
        self.lbl_new_pass1 = tk.Label(self, text="New Password", font=("Segoe UI", 9))
        self.lbl_new_pass1.pack(anchor="w", padx=35)
        self.new_pass_entry1 = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.new_pass_entry1.pack(fill="x", padx=35, pady=(0, 6), ipady=2)
        
        self.lbl_new_pass2 = tk.Label(self, text="Confirm New Password", font=("Segoe UI", 9))
        self.lbl_new_pass2.pack(anchor="w", padx=35)
        self.new_pass_entry2 = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.new_pass_entry2.pack(fill="x", padx=35, pady=(0, 8), ipady=2)
        
        self.btn_up_pass = tk.Button(self, text="Update Password", font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white", bd=0, pady=5, cursor="hand2",
                  command=self.ChangePassword)
        self.btn_up_pass.pack(fill="x", padx=35, pady=(0, 8))
        
        # Clear Inputs & Back Buttons
        self.clear_btn = tk.Button(self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white", bd=0, pady=4, cursor="hand2",
                  command=self.clear_inputs)
        self.clear_btn.pack(fill="x", padx=35, pady=(0, 6))
                  
        self.back_btn = tk.Button(self, text="Back to Tables", font=("Segoe UI", 9), bd=0, pady=4, cursor="hand2",
                  command=lambda: controller.show_frame(LoadTablesPage))
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
                for sub in widget.winfo_children():
                    if isinstance(sub, tk.Label):
                        sub.configure(bg=t["bg"], fg=t["fg"])
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
        
        jsonfile = {
            "action": "change_username",
            "current_username": current_username,
            "new_username": new_username
        }
        data = (json.dumps(jsonfile) + "\n").encode("utf-8") 
        
        try:
            self.controller.client_socket.sendall(data)       
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
                
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "Username successfully updated! Please sign in again.")
                self.clear_inputs()
                self.controller.client_socket.close()
                self.controller.show_frame(SignInPage)
            else:
                messagebox.showerror("Error", response.get("message", "Username change failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")

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
        
        jsonfile = {
            "action": "change_password",
            "current_password": current_password,
            "new_password": new_password
        }
        data = (json.dumps(jsonfile) + "\n").encode("utf-8") 
        
        try:
            self.controller.client_socket.sendall(data)       
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
                
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "Password successfully updated! Please sign in again.")
                self.clear_inputs()
                self.controller.client_socket.close()
                self.controller.show_frame(SignInPage)
            else:
                messagebox.showerror("Error", response.get("message", "Password change failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
        
    def DeleteUser(self):
        password = simpledialog.askstring("Confirm Deletion", "Enter your password to delete your account:", show='*')
        if not password:
            return
            
        jsonfile = {
            "action": "delete_user",
            "username": self.controller.current_username,
            "password": password
        }
        data = (json.dumps(jsonfile) + "\n").encode("utf-8") 
        
        try:
            self.controller.client_socket.sendall(data)       
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
                
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "User successfully deleted! Please sign up.")
                self.clear_inputs()
                if self.controller.client_socket:
                    try:
                        self.controller.client_socket.close()
                    except:
                        pass
                self.controller.show_frame(SignUpPage)
            else:
                messagebox.showerror("Error", response.get("message", "Deletion failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
        
class LoadTablesPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=30, pady=20)
        
        self.theme_btn = tk.Button(top_frame, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=self.controller.toggle_theme)
        self.theme_btn.pack(side="left")
        
        self.title_label = tk.Label(top_frame, text="Available Tables", font=("Segoe UI", 14, "bold"))
        self.title_label.pack(side="left", padx=15)
        
        self.settings_btn = tk.Button(top_frame, text="⚙ Settings", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2",
                  command=lambda: controller.show_frame(UserPage))
        self.settings_btn.pack(side="right")
        
        self.container_frame = tk.Frame(self)
        self.container_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.canvas = tk.Canvas(self.container_frame, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create Table Section
        self.create_frame = tk.Frame(self)
        self.create_frame.pack(fill="x", padx=30, pady=20)
        
        self.lbl_create = tk.Label(self.create_frame, text="Create New Table:", font=("Segoe UI", 10, "bold"))
        self.lbl_create.pack(anchor="w", pady=(0, 5))
        self.table_name_entry = tk.Entry(self.create_frame, font=("Segoe UI", 11), bd=0, relief="flat")
        self.table_name_entry.pack(fill="x", pady=(0, 10), ipady=4)

        self.btn_create = tk.Button(self.create_frame, text="Create & Join", font=("Segoe UI", 10, "bold"), bg="#0ae20a", fg="white", bd=0, pady=8, cursor="hand2",
                command=self.CreateTable)
        self.btn_create.pack(fill="x", pady=(0, 5))

        self.clear_btn = tk.Button(self.create_frame, text="Clear Input", font=("Segoe UI", 9), bg="#6c757d", fg="white", bd=0, pady=4, cursor="hand2",
                command=self.clear_inputs)
        self.clear_btn.pack(fill="x")

    def clear_inputs(self):
        self.table_name_entry.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        top_frame = self.winfo_children()[0]
        top_frame.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])
        self.settings_btn.configure(bg=t["card_bg"], fg=t["fg"])
        
        self.container_frame.configure(bg=t["bg"])
        self.canvas.configure(bg=t["card_bg"])
        self.scrollable_frame.configure(bg=t["card_bg"])
        
        self.create_frame.configure(bg=t["bg"])
        self.lbl_create.configure(bg=t["bg"], fg=t["fg"])
        self.table_name_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])
        self.refresh_tables()

    def refresh_tables(self):
        t = self.controller.themes[self.controller.current_theme]
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        tables = getattr(self.controller, "open_tables", [])
        if not tables:
            tk.Label(self.scrollable_frame, text="No tables available.", font=("Segoe UI", 11), fg="gray", bg=t["card_bg"]).pack(pady=30)
            return
            
        current_user = getattr(self.controller, "current_username", "")
        my_created = getattr(self.controller, "my_created_tables", set())
        
        for item in tables:
            if isinstance(item, dict):
                t_name = item.get("name") or item.get("table_name", "")
                t_creator = item.get("creator") or item.get("owner", "")
            else:
                t_name = str(item)
                t_creator = ""
                
            row_frame = tk.Frame(self.scrollable_frame, bg=t["card_bg"], bd=0, relief="flat")
            row_frame.pack(fill="x", padx=10, pady=6, ipadx=8, ipady=6)
            
            name_label = tk.Label(row_frame, text=t_name, font=("Segoe UI", 11, "bold"), fg=t["fg"], bg=t["card_bg"], anchor="w")
            name_label.pack(side="left", padx=10, fill="x", expand=True)
            
            join_btn = tk.Button(row_frame, text="Join", font=("Segoe UI", 9, "bold"), bg="#28a745", fg="white", bd=0, padx=12, pady=4, cursor="hand2",
                                 command=lambda name=t_name: self.JoinTable(name))
            join_btn.pack(side="right", padx=5)
            
            is_creator = False
            if t_creator and t_creator == current_user:
                is_creator = True
            elif not t_creator and t_name in my_created:
                is_creator = True
                
            if is_creator:
                delete_btn = tk.Button(row_frame, text="Delete", font=("Segoe UI", 9, "bold"), bg="#dc3545", fg="white", bd=0, padx=10, pady=4, cursor="hand2",
                                     command=lambda name=t_name: self.DeleteTable(name))
                delete_btn.pack(side="right", padx=5)
            
    def CreateTable(self):
        new_table_name = self.table_name_entry.get().strip()
        
        if not new_table_name:
            messagebox.showerror("Error", "Table name cannot be empty.")
            return
            
        try:
            payload = {
                "action": "create_table",
                "table_name": new_table_name
            }
            data = (json.dumps(payload) + "\n").encode("utf-8")
            
            self.controller.client_socket.sendall(data)
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
                      
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", f"Table '{new_table_name}' created successfully!")
                self.clear_inputs()
                if new_table_name not in self.controller.open_tables:
                    self.controller.open_tables.append(new_table_name)
                
                if not hasattr(self.controller, "my_created_tables"):
                    self.controller.my_created_tables = set()
                self.controller.my_created_tables.add(new_table_name)
                
                self.refresh_tables()
                self.controller.show_frame(GamePage)
            else:
                messagebox.showerror("Server Error", response.get("message", "Could not create table."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

    def JoinTable(self, selected_table_name):
        try:
            payload = {
                "action": "join_table",
                "table_name": selected_table_name
            }
            data = (json.dumps(payload) + "\n").encode("utf-8")
            
            self.controller.client_socket.sendall(data)
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
            
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", f"Successfully joined {selected_table_name}!")
                self.clear_inputs()
                self.controller.show_frame(GamePage)
            else:
                messagebox.showerror("Server Error", response.get("message", "Could not join table."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

    def DeleteTable(self, selected_table_name):
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete table '{selected_table_name}'?"):
            return
            
        try:
            payload = {
                "action": "delete_table",
                "table_name": selected_table_name
            }
            data = (json.dumps(payload) + "\n").encode("utf-8")
            
            self.controller.client_socket.sendall(data)
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8").strip()
            
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
            
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", f"Table '{selected_table_name}' deleted successfully!")
                
                if selected_table_name in self.controller.open_tables:
                    self.controller.open_tables.remove(selected_table_name)
                
                if hasattr(self.controller, "my_created_tables") and selected_table_name in self.controller.my_created_tables:
                    self.controller.my_created_tables.remove(selected_table_name)
                    
                self.refresh_tables()
            else:
                messagebox.showerror("Server Error", response.get("message", "Could not delete table."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

class SignUpPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  
        
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        self.theme_btn = tk.Button(top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=self.controller.toggle_theme)
        self.theme_btn.pack(side="left")
        
        self.title_label = tk.Label(self, text="Create Account", font=("Segoe UI", 18, "bold"))
        self.title_label.pack(pady=30)
        
        self.lbl_user = tk.Label(self, text="Choose Username", font=("Segoe UI", 10))
        self.lbl_user.pack(anchor="w", padx=35)
        self.user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.user_entry.pack(fill="x", padx=35, pady=(0, 12), ipady=4)
        
        self.lbl_pass = tk.Label(self, text="Choose Password", font=("Segoe UI", 10))
        self.lbl_pass.pack(anchor="w", padx=35)
        self.pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.pass_entry.pack(fill="x", padx=35, pady=(0, 20), ipady=4)
        
        self.signup_btn = tk.Button(self, text="Sign Up", font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white", bd=0, pady=10, cursor="hand2",
                  command=self.SignNewUser)
        self.signup_btn.pack(fill="x", padx=35, pady=5)

        self.clear_btn = tk.Button(self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white", bd=0, pady=6, cursor="hand2",
                  command=self.clear_inputs)
        self.clear_btn.pack(fill="x", padx=35, pady=(0, 10))
        
        self.switch_btn = tk.Button(self, text="Already have an account? Sign In", font=("Segoe UI", 9), bd=0, fg="#007acc", cursor="hand2",
                  command=lambda: controller.show_frame(SignInPage))
        self.switch_btn.pack(pady=10)

    def clear_inputs(self):
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        self.winfo_children()[0].configure(bg=t["bg"])
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
        
        jsonfile = {
            "action": "signup",
            "username": username,
            "password": password
        }
        data = (json.dumps(jsonfile) + "\n").encode("utf-8") 
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            client_socket.sendall(data)       
            server_response_raw = client_socket.recv(4096).decode("utf-8").strip()
            client_socket.close()
            
            if not server_response_raw:
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return
                
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "Account created successfully! Please sign in.")
                self.clear_inputs()
                self.controller.show_frame(SignInPage)
            else:
                messagebox.showerror("Error", response.get("message", "Signup failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")

class SignInPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        self.theme_btn = tk.Button(top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=self.controller.toggle_theme)
        self.theme_btn.pack(side="left")
        
        self.title_label = tk.Label(self, text="Welcome Back", font=("Segoe UI", 18, "bold"))
        self.title_label.pack(pady=30)
        
        self.lbl_user = tk.Label(self, text="Username", font=("Segoe UI", 10))
        self.lbl_user.pack(anchor="w", padx=35)
        self.user_entry = tk.Entry(self, font=("Segoe UI", 11), bd=0, relief="flat")
        self.user_entry.pack(fill="x", padx=35, pady=(0, 12), ipady=4)
        
        self.lbl_pass = tk.Label(self, text="Password", font=("Segoe UI", 10))
        self.lbl_pass.pack(anchor="w", padx=35)
        self.pass_entry = tk.Entry(self, font=("Segoe UI", 11), show="*", bd=0, relief="flat")
        self.pass_entry.pack(fill="x", padx=35, pady=(0, 20), ipady=4)
        
        self.signin_btn = tk.Button(self, text="Sign In", font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white", bd=0, pady=10, cursor="hand2",
                  command=self.SignOldUser)
        self.signin_btn.pack(fill="x", padx=35, pady=5)

        self.clear_btn = tk.Button(self, text="Clear Inputs", font=("Segoe UI", 9), bg="#6c757d", fg="white", bd=0, pady=6, cursor="hand2",
                  command=self.clear_inputs)
        self.clear_btn.pack(fill="x", padx=35, pady=(0, 10))
        
        self.switch_btn = tk.Button(self, text="Dont have an account? Sign Up", font=("Segoe UI", 9), bd=0, fg="#007acc", cursor="hand2",
                  command=lambda: controller.show_frame(SignUpPage))
        self.switch_btn.pack(pady=10)

    def clear_inputs(self):
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        self.configure(bg=t["bg"])
        self.winfo_children()[0].configure(bg=t["bg"])
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
                
        jsonfile = {
            "action": "signin",
            "username": username,
            "password": password
        }
        data = (json.dumps(jsonfile) + "\n").encode("utf-8") 
                
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))   
            client_socket.sendall(data)
            server_response_raw = client_socket.recv(4096).decode("utf-8").strip()    
            
            if not server_response_raw:
                client_socket.close()
                messagebox.showerror("Server Error", "Server sent an empty response.")
                return

            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                self.controller.client_socket = client_socket
                
                self.controller.current_username = response.get("username", username)
                self.controller.player_balance = response.get("balance", 0)
                raw_tables = response.get("open_tables", [])
                
                self.controller.my_created_tables = set()
                clean_tables = []
                for t in raw_tables:
                    if isinstance(t, dict):
                        name = t.get("name") or t.get("table_name")
                        creator = t.get("creator") or t.get("owner")
                        if name:
                            clean_tables.append(name)
                            if creator == self.controller.current_username:
                                self.controller.my_created_tables.add(name)
                    else:
                        clean_tables.append(str(t))
                        
                self.controller.open_tables = clean_tables
                
                messagebox.showinfo("Success", f"Welcome back, {self.controller.current_username}! Chips: {self.controller.player_balance}")
                self.clear_inputs()
                self.controller.show_frame(LoadTablesPage)
            else:
                client_socket.close()
                messagebox.showerror("Error", response.get("message", "Signin failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            
class GamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", padx=25, pady=15)
        self.theme_btn = tk.Button(top_bar, text="", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=self.controller.toggle_theme)
        self.theme_btn.pack(side="left")
        
        self.title_label = tk.Label(self, text="Poker Table Arena", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(pady=90)
        
        self.status_label = tk.Label(self, text="", font=("Segoe UI", 13, "bold"), fg="yellow")
        self.status_label.pack(pady=10)
        
        self.leave_btn = tk.Button(self, text="Leave Table", font=("Segoe UI", 10, "bold"), bg="#dc3545", fg="white", bd=0, padx=20, pady=10, cursor="hand2",
                  command=lambda: controller.show_frame(LoadTablesPage))
        self.leave_btn.pack(side="bottom", pady=40)

    def apply_theme(self):
        t = self.controller.themes[self.controller.current_theme]
        bg_color = "#0f4c22" if self.controller.current_theme == "dark" else t["bg"]
        self.configure(bg=bg_color)
        self.winfo_children()[0].configure(bg=bg_color)
        self.title_label.configure(bg=bg_color, fg=t["fg"])
        self.status_label.configure(bg=bg_color)
        self.theme_btn.configure(text=t["toggle_text"], bg=t["card_bg"], fg=t["fg"])

    def tkraise(self, aboveThan=None):
        super().tkraise(aboveThan)
        username = getattr(self.controller, "current_username", "Player")
        balance = getattr(self.controller, "player_balance", 0)
        self.status_label.config(text=f"User: {username}  |  Chips: ${balance}")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()