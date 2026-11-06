import enum
from game_files.card import Deck
from game_files.table import Table
from game_files.dealer import Dealer
from game_files.player import Player

class Round:
    
    def __init__(self, table: Table):
        self.roundStage = RoundStage.PRE_FLOP
        self.table = table
        self.current_bet = 0
        self.pot = 0
        self.active_players = [player for player in table.players if player.isLoggedIn]
        self.currentPlayerTurnIndex = 0

    def start_round(self):
        if len(self.active_players) < 2:
            raise ValueError("Not enough players to start the round.")
        self.table.dealer.ShuffleDeck()
        for player in self.active_players:
            player.currentHand = [self.table.dealer.DealCard(), self.table.dealer.DealCard()]

    def advance_stage(self):
        if self.roundStage == RoundStage.PRE_FLOP:
            self.roundStage = RoundStage.FLOP
            for card in range(3):
                self.table.dealer.DealTableCards()
        elif self.roundStage == RoundStage.FLOP:
            self.roundStage = RoundStage.TURN
            self.table.dealer.DealTableCards()
        elif self.roundStage == RoundStage.TURN:
            self.roundStage = RoundStage.RIVER
            self.table.dealer.DealTableCards()
        elif self.roundStage == RoundStage.RIVER:
            self.roundStage = RoundStage.SHOWDOWN
        else:
            raise ValueError("Round has already reached the SHOWDOWN stage.")

    def get_current_player(self):
        if not self.active_players:
            raise ValueError("No active players left in the round.")
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = True
        return self.active_players[self.currentPlayerTurnIndex]

    def next_player_turn(self):
        if not self.active_players:
            raise ValueError("No active players left in the round.")
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = False
        self.currentPlayerTurnIndex = (self.currentPlayerTurnIndex + 1) % len(self.active_players)
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = True

    def remove_folded_players(self):
        self.active_players = [player for player in self.active_players if not player.isFolded]
        if self.currentPlayerTurnIndex >= len(self.active_players):
            self.currentPlayerTurnIndex = 0

    def add_to_pot(self):
        if self.current_bet < 0:
            raise ValueError("Amount to add to pot cannot be negative.")
        self.pot += self.current_bet

    def reset_game(self):
        self.roundStage = RoundStage.PRE_FLOP
        self.current_bet = 0
        self.pot = 0
        self.active_players = [player for player in self.table.players if player.isLoggedIn]
        self.currentPlayerTurnIndex = 0
        for player in self.active_players:
            player.isFolded = False
            player.isPlayerTurn = False
            player.currentHand = []
            player.UpdateUserBalance(player.username, player.currentBalance)  # Ensure balance is updated in the database
        self.table.dealer.currentDeck = Deck()
        self.table.dealer.tableCards = Deck()




class RoundStage(enum.Enum):
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"