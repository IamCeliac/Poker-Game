import sqlite3
from game_files.player import Player

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.isLoggedIn = False
        print('User Created Succesfully')

    def GetUsername(self):
        return self.username
  
  
    def IsUserUnique(self,username):

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE username = ?",
            (username,)
        )
        foundUsername = cursor.fetchone()
        conn.commit()
        conn.close()
        return foundUsername is None
         

    def CreateNewUser(self):
        # Create a new user in the database
        if self.IsUserUnique(self.username):
            conn  = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password,balance) VALUES (?, ?,?)", 
                (self.username, self.password,500)
            )
            conn.commit()
            conn.close()
            return True
        else: raise ValueError("Username Taken!")

   
    def LogIntoUser(self):
            
            # Check if a user with the given credentials exists in the database
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?", 
                (self.username, self.password)
            )
            user = cursor.fetchone()
            if user is None:
                conn.close()
                raise ValueError("Invalid username or password.")

            if user[4] == 1:
                conn.close()
                raise ValueError("This user is already logged in!")

            
            cursor.execute(
                "UPDATE users SET isLoggedIn = 1 WHERE username = ?", 
                (self.username,)
            )
            
            conn.commit()
            conn.close()
            
            print(f"User {self.username} logged in successfully.")
            return Player(self.username,self.GetUserBalance())
            

    @staticmethod
    def LogOutUser(player:Player):
        # Log out a user by updating the isLoggedIn status in the database
       
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = ? ,isLoggedIn = 0 WHERE username = ?", 
            (player.currentBalance,player.username,)
        )
        conn.commit()
        conn.close()

    @staticmethod
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

    
    def GetUserBalance(self):
       
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance, isLoggedIn FROM users WHERE username = ?",
            (self.username,)
        )
        output = cursor.fetchone()
        conn.close()
        if output is None: 
            raise ValueError("User does not exist.")
        balance,isLoggedIn = output[0],output[1]
        if isLoggedIn == 1: 
            return balance
        else:
            raise ValueError("User is not logged in. Please log in to view balance.")

    @staticmethod
    def UpdateUserBalance(username, new_balance):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = ? WHERE username = ?", 
            (new_balance, username)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def UpdateUsername(username,newUsername):
        if (username == newUsername):
            raise ValueError("new username must be different from last username.")
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ? WHERE username = ?",
            (newUsername,username)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def UpdateUserPassword(username,currentPassword,newPassword):
            if (currentPassword == newPassword):
                raise ValueError("Password must be different from last password.")


            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute(
                "SELECT username FROM users WHERE username = ? AND password = ?",
                (username,currentPassword)
            )
            user = cursor.fetchone()
            if user is None:
                conn.close()
                raise ValueError("Entered password is not correct.")

            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (newPassword,username)
            )
            conn.commit()
            conn.close()

    
