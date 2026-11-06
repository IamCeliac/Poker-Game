from game_files.card import Card, Deck
from user_files.user import User
from game_files.table import Table

class Player(User):

    def __init__(self):
        self.playerName = super().GetUsername()
        self.currentBalance = super().GetUserBalance(self.playerName)
        self.isPlayerTurn = False
        self.isFolded = False
        self.table = None
        self.currentHand = []


    def CreateTable(self, tableName):
        self.table = Table(tableName)
        self.table.add_player(self)

    def DeleteTable(self):
        if self.table is not None:
            self.table.remove_player(self)
            self.table = None
        else:
            raise ValueError("Player Did Not Create Any Table.")


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

    def AddToDeck(self, card):
        self.currentDeck.cards.append(card)

    def RemoveFromDeck(self, card):
        if card in self.currentDeck.cards:
            self.currentDeck.cards.remove(card)
        else:
            raise ValueError("Card not found in the player's deck.")

    def ExitGame(self):
        self.isPlayerTurn = False
        self.isFolded = False
        self.currentDeck.cards.clear()

    
       

        
