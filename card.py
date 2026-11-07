import enum

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
    
class Card:
    def __init__(self, cardNumber, cardSuit):
        self.cardNumber = cardNumber
        self.cardSuit = cardSuit


    def __repr__(self):
        return f"{self.cardNumber.value} of {self.cardSuit.value}" 
        # (Change self.rank and self.suit to whatever variable names you used in Card.__init__!)