import enum

class Deck():
    def __init__(self):
        self.cards = []
        for suit in CardSuit:
            for number in CardNumber:
                self.cards.append(Card(number, suit))
        self.shuffle()

    def shuffle(self):
        import random
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


class Card:
    def __init__(self, cardNumber, cardSuit):
        self.cardNumber = cardNumber
        self.cardSuit = cardSuit

    def __str__(self):
        return f"{self.cardNumber.value} of {self.cardSuit.value}"


class CardSuit(enum.Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"

class CardNumber(enum.Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = "Jack"
    QUEEN = "Queen"
    KING = "King"
    ACE = "Ace"