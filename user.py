import sqlite3

from game_files.player import Player
class User:

    uniqueId = 0
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.isLoggedIn = False
        User.uniqueId += 1
        self.uniqueId = User.uniqueId
        print('User Created Succesfully')

    def GetUsername(self):
        return self.username
    
    def GetUniqueId(self):
        return self.uniqueId
    
    def CreateNewUser(username, password,uniqueId):
        # Create a new user in the database

        conn  = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password,id,balance) VALUES (?, ?,?,?)", 
            (username, password, uniqueId,500)
        )
        conn.commit()
        conn.close()
        return User(username, password)

    def LogIntoUser(username, password):
            # Check if a user with the given credentials exists in the database
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?", 
                (username, password)
            )
            user = cursor.fetchone()
            if user is not None:
             cursor.execute(
                "UPDATE users SET isLoggedIn = 1 WHERE username = ?", 
                (username,)
            )
            
            conn.commit()
            conn.close()
            if user:
                print(f"User {username} logged in successfully.")
                return True
            else:
                raise ValueError("User not found. Please sign up.")

    def LogOutUser(username):
        # Log out a user by updating the isLoggedIn status in the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET isLoggedIn = 0 WHERE username = ?", 
            (username,)
        )
        conn.commit()
        conn.close()

    def DeleteUser(username):
        # Delete a user from the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE username = ?", 
            (username,)
        )
        conn.commit()
        conn.close()

    def GetUserBalance(username):
       
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance, isLoggedIn FROM users WHERE username = ?",
            (username,)
        )
        output = cursor.fetchone()
        conn.close()
        isLoggedIn = output[1]
        if isLoggedIn == 1: 
            return output[0]
        else:
            raise ValueError("User is not logged in. Please log in to view balance.")

    def UpdateUserBalance(username, new_balance):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = ? WHERE username = ?", 
            (new_balance, username)
        )
        conn.commit()
        conn.close()
