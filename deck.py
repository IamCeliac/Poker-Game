import enum
import random
from game_files.card import Card, CardSuit, CardNumber

class Deck():
    def __init__(self):
        self.cards = []
        for suit in CardSuit:
            for number in CardNumber:
                self.cards.append(Card(number, suit))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):
        if len(self.cards) == 0:
            raise ValueError("No more cards in the deck.")
        return self.cards.pop()

    def create_deckby_size(self, size):
        if size < 1 or size > 52:
            raise ValueError("Size must be between 1 and 52.")
        self.cards = []
        for suit in CardSuit:
            for number in CardNumber:
                self.cards.append(Card(number, suit))
        self.cards = self.cards[:size]
        self.shuffle()