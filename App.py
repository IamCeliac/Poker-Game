import tkinter as tk
from tkinter import messagebox
import socket 
import json
from server import SERVER_IP, SERVER_PORT

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Poker Game - Registration Page")
        self.geometry("380x450")
        self.configure(bg="black")
        
        self.current_username = ""
        self.player_balance = 0
        self.open_tables = []
        
        container = tk.Frame(self, bg="black")
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.socket = None
        
        self.frames = {}
        
        for PageClass in (SignInPage, SignUpPage, LoadTablesPage, GamePage):
            frame = PageClass(container, self)
            self.frames[PageClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame(SignInPage)
            
    def show_frame(self, page_class):
        frame = self.frames[page_class]
        if page_class == LoadTablesPage:
            frame.refresh_tables()
        frame.tkraise()
        
        
class LoadTablesPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="black")
        
        tk.Label(self, text="Available Poker Tables", font=("Arial", 16, "bold"), fg="white", bg="black").pack(pady=15)
        
        self.tables_listbox = tk.Listbox(self, font=("Arial", 12), bg="#222", fg="white", selectbackground="#007acc")
        self.tables_listbox.pack(fill="both", expand=True, padx=30, pady=10)
        
        tk.Label(self, text="Enter Table Index Number to Join:", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.index_entry = tk.Entry(self, font=("Arial", 12))
        self.index_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        tk.Button(self, text="Join Table", font=("Arial", 11, "bold"), bg="#28a745", fg="white", 
                command=self.JoinTable).pack(fill="x", padx=30, pady=(0, 20))
        
        tk.Label(self, text="Or Enter New Table Name to Create:", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.table_name_entry = tk.Entry(self, font=("Arial", 12))
        self.table_name_entry.pack(fill="x", padx=30, pady=(0, 10))

        tk.Button(self, text="Create Table", font=("Arial", 11, "bold"), bg="#0ae20a", fg="white", 
                command=self.CreateTable).pack(fill="x", padx=30, pady=(0, 20))

    def refresh_tables(self):
        self.tables_listbox.delete(0, tk.END)
        for idx, table_name in enumerate(self.controller.open_tables):
            self.tables_listbox.insert(tk.END, f"[{idx}] {table_name}")
            
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
            data = json.dumps(payload).encode("utf-8")
            
            self.controller.client_socket.sendall(data)
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8")  
                      
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", f"Table '{new_table_name}' created successfully!")
                self.controller.open_tables.append(new_table_name)
                self.refresh_tables()
                self.table_name_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Server Error", response.get("message", "Could not create table."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

    def JoinTable(self):
        entered_text = self.index_entry.get().strip()
        
        if not entered_text.isdigit():
            messagebox.showerror("Error", "Please enter a valid numeric index.")
            return
            
        index = int(entered_text)
        
        if index < 0 or index >= len(self.controller.open_tables):
            messagebox.showerror("Error", "Invalid table index selected.")
            return
            
        selected_table_name = self.controller.open_tables[index]
        
        try:
            payload = {
                "action": "join_table",
                "table_name": selected_table_name
            }
            data = json.dumps(payload).encode("utf-8")
            
            self.controller.client_socket.sendall(data)
            server_response_raw = self.controller.client_socket.recv(4096).decode("utf-8")
            
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", f"Successfully joined {selected_table_name}!")
                self.controller.show_frame(GamePage)
            else:
                messagebox.showerror("Server Error", response.get("message", "Could not join table."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
        
class GamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="green") 
        
        tk.Label(self, text="Welcome to the Poker Table!", font=("Arial", 22, "bold"), fg="white", bg="green").pack(pady=100)
        
        self.status_label = tk.Label(self, text="", font=("Arial", 14), fg="yellow", bg="green")
        self.status_label.pack(pady=10)

    def tkraise(self, aboveThan=None):
        super().tkraise(aboveThan)
        username = getattr(self.controller, "current_username", "Player")
        balance = getattr(self.controller, "player_balance", 0)
        self.status_label.config(text=f"User: {username}  |  Chips: ${balance}")

class SignUpPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  
        self.configure(bg="black")
        
        tk.Label(self, text="Create Account", font=("Arial", 18, "bold"), fg="white", bg="black").pack(pady=25)
        
        tk.Label(self, text="Choose Username", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.user_entry = tk.Entry(self, font=("Arial", 12))
        self.user_entry.pack(fill="x", padx=30, pady=(0, 10))
        
        tk.Label(self, text="Choose Password", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.pass_entry = tk.Entry(self, font=("Arial", 12), show="*")
        self.pass_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        tk.Button(self, text="Sign Up", font=("Arial", 11, "bold"), bg="#28a745", fg="white", 
                  command=self.SignNewUser).pack(fill="x", padx=30, pady=5)
        
        tk.Button(self, text="Already have an account? Sign In", font=("Arial", 9), bd=0, fg="#007acc", bg="black", 
                  command=lambda: controller.show_frame(SignInPage)).pack(pady=10)

    def SignNewUser(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        jsonfile = {
            "action": "signup",
            "username": username,
            "password": password
        }
        data = json.dumps(jsonfile).encode("utf-8") 
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            client_socket.sendall(data)       
            server_response_raw = client_socket.recv(4096).decode("utf-8")
            client_socket.close()
                
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                messagebox.showinfo("Success", "Account created successfully! Please sign in.")
                self.controller.show_frame(SignInPage)
            else:
                messagebox.showerror("Error", response.get("message", "Signup failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
        


class SignInPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Save controller reference
        self.configure(bg="black")
        
        tk.Label(self, text="Welcome Back", font=("Arial", 18, "bold"), fg="white", bg="black").pack(pady=25)
        
        tk.Label(self, text="Username", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.user_entry = tk.Entry(self, font=("Arial", 12))
        self.user_entry.pack(fill="x", padx=30, pady=(0, 10))
        
        tk.Label(self, text="Password", font=("Arial", 10), fg="white", bg="black").pack(anchor="w", padx=30)
        self.pass_entry = tk.Entry(self, font=("Arial", 12), show="*")
        self.pass_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        tk.Button(self, text="Sign In", font=("Arial", 11, "bold"), bg="#28a745", fg="white", 
                  command=self.SignOldUser).pack(fill="x", padx=30, pady=5)
        
        tk.Button(self, text="Dont have an account? Sign Up", font=("Arial", 9), bd=0, fg="#007acc", bg="black", 
                  command=lambda: controller.show_frame(SignUpPage)).pack(pady=10)

    def SignOldUser(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
                
        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
                
        jsonfile = {
            "action": "signin",
            "username": username,
            "password": password
        }
        data = json.dumps(jsonfile).encode("utf-8") 
                
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))   
            client_socket.sendall(data)
            server_response_raw = client_socket.recv(4096).decode("utf-8")    
            
            response = json.loads(server_response_raw)
            if response.get("status") == "ok":
                self.controller.client_socket = client_socket
                
                self.controller.current_username = response.get("username", username)
                self.controller.player_balance = response.get("balance", 0)
                self.controller.open_tables = response.get("open_tables", [])
                
                messagebox.showinfo("Success", f"Welcome back, {self.controller.current_username}! Chips: {self.controller.player_balance}")
                self.controller.show_frame(LoadTablesPage)
            else:
                messagebox.showerror("Error", response.get("message", "Signin failed."))
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()