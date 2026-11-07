import sqlite3

class Database:
    def __init__(self, db_name):
        # Runs automatically when you instantiate the class
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            balance INTEGER,
            isLoggedIn BOOLEAN DEFAULT 0
        )
        """
        self.cursor.execute(query)
        self.conn.commit()
        print("Table created successfully.")

    def reset_all_logins(self):
        """Run this once when server.py starts to clear any stuck logins from crashes."""
        self.cursor.execute("UPDATE users SET isLoggedIn = 0")
        self.conn.commit()
   

        



