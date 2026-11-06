import enum
from random import random 
from game_files.card import Deck


class Dealer:

    def __init__(self):
        self.name = random.choice(list(DealerNames)).value
        self.currentDeck = Deck()
        self.tableCards = Deck()


    def ShuffleDeck(self):
        self.currentDeck.shuffle()

    def DealCard(self):
        if len(self.currentDeck.cards) == 0:
            self.currentDeck.shuffle()  
        return self.currentDeck.draw_card()

    def DealTableCards(self):
        if len(self.tableCards.cards) >= 5:
            raise ValueError("Maximum of 5 table cards already dealt.")
        self.tableCards.append(self.currentDeck.draw_card())


class DealerNames(enum.Enum):
    Alice = "Alice"
    Bob = "Bob"
    Jake = "Jake"
    David = "David"
    Lucas = "Lucas"
    Yannai = "Yannai"
    Noam = "Noam"


