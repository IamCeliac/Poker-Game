import sqlite3
import socket
import json
from game_files.player import Player

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.isLoggedIn = False
        print('User Created Succesfully')

    def GetUsername(self):
        return self.username
    
    def GetUniqueId(self):
        return self.uniqueId
    
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
            if user is not None:
             cursor.execute(
                "UPDATE users SET isLoggedIn = 1 WHERE username = ?", 
                (self.username,)
            )
            
            conn.commit()
            conn.close()
            if user:
                print(f"User {self.username} logged in successfully.")
                return Player(self.username,self.GetUserBalance(self.username))
            else:
                raise ValueError("User not found. Please sign up.")

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

    
    def GetUserBalance(self,username):
       
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
