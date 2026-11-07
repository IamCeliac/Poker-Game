import enum
from game_files.deck import Deck
from game_files.table import Table
from game_files.dealer import Dealer
from game_files.player import Player
from user_files.user import User 

class RoundStage(enum.Enum):
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"

class Round:
    
    def __init__(self, table: Table):
        self.roundStage = RoundStage.PRE_FLOP
        self.table = table
        self.current_bet = 0
        self.pot = 0
        self.active_players = [player for player in table.players]
        self.currentPlayerTurnIndex = 0

    def start_round(self):
        if len(self.active_players) < 2:
            raise ValueError("Not enough players to start the round.")
        self.table.dealer.ShuffleDeck()
        for player in self.active_players:
            player.isPlayerTurn = False
            player.currentHand = [self.table.dealer.DealCard(), self.table.dealer.DealCard()]

        self.currentPlayerTurnIndex = 0
        self.active_players[0].isPlayerTurn = True

    def advance_stage(self):
        if self.roundStage == RoundStage.PRE_FLOP:
            self.roundStage = RoundStage.FLOP
            for _ in range(3):
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

    def handle_player_action(self, player, action, amount=0):
        """Processes a player's move, adds chips to the pot, and moves to the next turn."""
        if not player.isPlayerTurn:
            raise ValueError(f"It is not {player.username}'s turn!")

        if action == "bet" or action == "call" or action == "raise":
            chips = player.PlaceBet(amount)
            self.current_bet = amount
            self.pot += chips
            print(f"{player.username} put {chips} in the pot. Total pot: {self.pot}")
        elif action == "fold":
            player.Fold()
            print(f"{player.username} folded.")
        elif action == "check":
            print(f"{player.username} checked.")

        # Automatically pass the turn to the next active player!
        self.next_player_turn()
        print(f"Next turn: {self.get_current_player().username}")

    def next_player_turn(self):
        # 1. Turn off current player's turn
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = False

        # 2. Check how many players haven't folded yet
        unfolded_players = [p for p in self.active_players if not p.isFolded]
        if len(unfolded_players) <= 1:
            # Everyone else folded! Hand is over.
            print(f"{unfolded_players[0].username} wins the pot of {self.pot}!")
            unfolded_players[0].currentBalance += self.pot
            self.reset_game()
            return

        # 3. Loop to the next player until we find one who hasn't folded
        while True:
            self.currentPlayerTurnIndex = (self.currentPlayerTurnIndex + 1) % len(self.active_players)
            next_player = self.active_players[self.currentPlayerTurnIndex]
            if not next_player.isFolded:
                next_player.isPlayerTurn = True
                break

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
        self.active_players = [player for player in self.table.players]
        self.currentPlayerTurnIndex = 0
        for player in self.active_players:
            player.isFolded = False
            player.isPlayerTurn = False
            player.currentHand = []
            User.UpdateUserBalance(player.username, player.currentBalance)  # Ensure balance is updated in the database
        self.table.dealer.currentDeck = Deck()
        self.table.dealer.tableCards = Deck()
