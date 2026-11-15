import enum
import random 
from game_files.deck import Deck
from game_files.card import Card

class Dealer:

    def __init__(self):
        self.name = random.choice(list(DealerNames)).value
        self.currentDeck = Deck()
        self.tableCards : list[Card] = []

    def ShuffleDeck(self):
        self.currentDeck.shuffle()

    def ResetDealer(self):
        self.currentDeck = Deck()
        self.tableCards = []

    def DealCard(self):
        if len(self.currentDeck.cards) == 0:
            self.currentDeck = Deck()  
        return self.currentDeck.draw_card()

    def DealTableCards(self):
        if len(self.tableCards) >= 5:
            raise ValueError("Maximum of 5 table cards already dealt.")
        self.tableCards.append(self.currentDeck.draw_card())


    @staticmethod
    def evaluate_5_cards(cards: list[Card]) -> tuple:
        values = sorted([c.get_value() for c in cards],reverse=True)
        suits = [c.cardSuit for c in cards]

        is_flush = len(set(suits)) == 1

        # Check normal straight
        is_straight = (values == list(range(values[0],values[0]-5,-1)))
        if values == [14,5,4,3,2]:
            is_straight = True
            values = [5,4,3,2,1]

        # Count frequencies
        counts = {}
        for v in values:
            counts[v] = counts.get(v,0)+1

        sorted_vals = sorted(counts.keys(),key =lambda v: (counts[v],v),reverse=True)
        freqs = sorted(counts.values(), reverse=True)

        if is_straight and is_flush:
            return (8, values)          # Straight Flush
        if freqs == [4, 1]:
            return (7, sorted_vals)     # Four of a Kind
        if freqs == [3, 2]:
            return (6, sorted_vals)     # Full House
        if is_flush:
            return (5, values)          # Flush
        if is_straight:
            return (4, values)          # Straight
        if freqs == [3, 1, 1]:
            return (3, sorted_vals)     # Three of a Kind
        if freqs == [2, 2, 1]:
            return (2, sorted_vals)     # Two Pair
        if freqs == [2, 1, 1, 1]:
            return (1, sorted_vals)     # One Pair
        return (0, values)              # High Card


    def get_best_hand(self, hole_cards: list[Card]) -> tuple:
        seven_cards = hole_cards + self.tableCards
        best_score = None

        # Pick 2 indices (i and j) to exclude from the 7 cards to get every 5-card combo
        for i in range(len(seven_cards)):
            for j in range(i + 1, len(seven_cards)):
                five_cards = [
                    seven_cards[k] for k in range(len(seven_cards))
                    if k != i and k != j
                ]
                score = self.evaluate_5_cards(five_cards)
                if best_score is None or score > best_score:
                    best_score = score

        return best_score

        


class DealerNames(enum.Enum):
    Alice = "Alice"
    Bob = "Bob"
    Jake = "Jake"
    David = "David"
    Lucas = "Lucas"
    Yannai = "Yannai"
    Noam = "Noam"


