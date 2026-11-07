from game_files.card import Card
from game_files.deck import Deck


class Player:

    def __init__(self,username,balance):
        self.username = username
        self.currentBalance = balance
        self.currentTableName = ''
        self.isPlayerTurn = False
        self.isFolded = False
        self.isTableCreated = False
        self.isLoggedIn = True
        self.currentHand: list[Card] = []


    def PlaceBet(self, betAmount):
        if self.isPlayerTurn is False or self.isFolded is True:
            raise ValueError("Player cannot place a bet at this time.")
        if betAmount > self.currentBalance and self.currentBalance > 0:
            raise ValueError("Insufficient balance to place the bet.")
        if self.isFolded:
            raise ValueError("Player has folded and cannot place a bet.")
        self.currentBalance -= betAmount
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
        return allInAmount

    def CreateTable(self, tableName):

        from game_files.game import Game
        from game_files.table import Table

        if not self.isTableCreated:
            self.currentTableName = tableName
            table = Table(tableName)
            table.add_player(self)
            Game.openTables.append(table)
            self.isTableCreated = True
        else: raise ValueError("Player Already Created Table!")

    
    def DeleteTable(self):
        from game_files.game import Game

        if self.isTableCreated:
            tableToRemove = self.RemovePlayerFromTable()
            Game.openTables.remove(tableToRemove)
            self.isTableCreated = False
        else:
            raise ValueError("Player Did Not Create Any Table.")


    def RemovePlayerFromTable(self):
            from game_files.game import Game
            for table in Game.openTables:
                if table.tableName == self.currentTableName:
                    table.remove_player(self)
                    self.currentTableName = ''
                    return table

    def AddToHand(self, card):
        self.currentHand.append(card)

    def RemoveFromHand(self, card):
        if card in self.currentHand.cards:
            self.currentHand.cards.remove(card)
        else:
            raise ValueError("Card not found in the player's deck.")

    def ExitGame(self):

        self.isPlayerTurn = False
        self.isFolded = False
        self.currentHand.cards.clear()


    

    
       

        
