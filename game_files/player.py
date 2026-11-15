from game_files.card import Card
from game_files.deck import Deck


class Player:

    def __init__(self,username,balance):
        self.username = username
        self.currentBalance = balance
        self.currentStreetbet = 0
        self.currentTableName = ''
        self.isPlayerTurn = False
        self.isFolded = False
        self.isTableCreated = False
        self.isLoggedIn = True
        self.currentHand: list[Card] = []


    def PlaceBet(self, betAmount):
        if not self.isPlayerTurn or self.isFolded:
            raise ValueError("Player cannot place a bet at this time.")
        if betAmount <= 0:
            raise ValueError("Bet amound should be greater than 0")
        if betAmount > self.currentBalance:
            raise ValueError("Insufficient balance to place the bet.")
        self.currentBalance -= betAmount
        self.currentStreetbet += betAmount
        return betAmount

    def Fold(self):
        self.isFolded = True
        self.isPlayerTurn = False

    def Raise(self, raiseAmount):
        if self.isPlayerTurn is False or self.isFolded is True:
            raise ValueError("Player cannot place a bet at this time.")
        if raiseAmount > self.currentBalance and self.currentBalance > 0:
            raise ValueError("Insufficient balance to raise.")
        if self.isFolded:
            raise ValueError("Player has folded and cannot raise.")
        self.currentBalance -= raiseAmount
        return raiseAmount

    def Call(self, callAmount):
        if self.isPlayerTurn is False or self.isFolded is True:
            raise ValueError("Player cannot place a bet at this time.")
        if callAmount > self.currentBalance and self.currentBalance > 0:
            raise ValueError("Insufficient balance to call.")
        if self.isFolded:
            raise ValueError("Player has folded and cannot call.")
        self.currentBalance -= callAmount
        return callAmount

    def AllIn(self):
        if self.isPlayerTurn is False or self.isFolded is True:
            raise ValueError("Player cannot place a bet at this time.")
        if self.isFolded:
            raise ValueError("Player has folded and cannot go all-in.")
        allInAmount = self.currentBalance
        self.currentBalance = 0
        self.currentStreetbet += allInAmount
        return allInAmount

    def CreateTable(self, tableName):

        from game_files.game import Game
        from game_files.table import Table

        if not self.isTableCreated:
            if Game.GetTableByName(tableName) is not None:
                raise ValueError("Table already exists!")
            
            self.currentTableName = tableName
            table = Table(tableName,self.username)
            table.add_player(self)
            Game.openTables.append(table)
            self.isTableCreated = True
            return table
        else: 
            raise ValueError("Player Already Created Table!")

    def ChangeUsername(self,username, newUsername):
        from user_files.user import User
        self.username = newUsername
        User.UpdateUsername(username,newUsername)
        print(f"Username: {username} updated to {newUsername} successfully")

    def ChangePassword(self,currentPassword,newPassword):
        from user_files.user import User
        User.UpdateUserPassword(self.username,currentPassword,newPassword)
        print(f"User:{self.username} password updated successfully!")

    
    def DeleteTable(self, tableName=None):
        from game_files.game import Game

        target_tableName = tableName or self.currentTableName
        tableToRemove = Game.GetTableByName(target_tableName)

        if tableToRemove is None:
            raise ValueError("Table doesn't exist")

        if tableToRemove.creator != self.username or not self.isTableCreated:
            raise ValueError("You can only delete your table!")

        for p in list(tableToRemove.players):
            p.currentTableName = ""
            tableToRemove.remove_player(p)

        if tableToRemove in Game.openTables:
            Game.openTables.remove(tableToRemove)

        self.isTableCreated = False
        if self.currentTableName == target_tableName:
            self.currentTableName = ""


    def RemovePlayerFromTable(self):
        from game_files.game import Game

        for table in list(Game.openTables):
            if table.tableName == self.currentTableName:
                table.remove_player(self)
                self.currentTableName = ''
                if table not in Game.openTables and table.creator == self.username:
                    self.isTableCreated = False
                return table

    def AddToHand(self, card):
        self.currentHand.append(card)

    def RemoveFromHand(self, card):
        if card in self.currentHand:
            self.currentHand.remove(card)
        else:
            raise ValueError("Card not found in the player's deck.")

    def ExitGame(self):

        self.isPlayerTurn = False
        self.isFolded = False
        self.currentHand.clear()


    

    
       

        
