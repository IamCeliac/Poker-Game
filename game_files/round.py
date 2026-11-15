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

        self.current_bet = 0

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

    def handle_player_action(self, player: Player, action, amount=0):
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
        elif action == "all_in":
            chips = player.AllIn()
            self.current_bet = chips
            self.pot += chips
            print(f"{player.username} is All in with {chips}. Total pot: {self.pot}")
        elif action == "check":
            print(f"{player.username} checked.")

        # Automatically pass the turn to the next active player!
        self.next_player_turn()
        

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

        while True:
            self.currentPlayerTurnIndex = (self.currentPlayerTurnIndex+1) % len(self.active_players)
            next_player = self.active_players[self.currentPlayerTurnIndex]
            if not next_player.isFolded:
                next_player.isPlayerTurn = True
                print(f"Next turn: {next_player.username}")
                break

        # 3. Loop to the next player until we find one who hasn't folded
        while True:
            self.currentPlayerTurnIndex = (self.currentPlayerTurnIndex + 1) % len(self.active_players)
            next_player = self.active_players[self.currentPlayerTurnIndex]
            if not next_player.isFolded:
                next_player.isPlayerTurn = True
                break

    def get_state_for_player(self, viewer_player):
        """
        Converts the current Round state into a JSON-friendly dictionary
        tailored for 'viewer_player' (hiding opponents' hole cards until Showdown).
        """
        # 1. Convert community cards on the table to strings
        if hasattr(self.table.dealer.tableCards, "cards"):
            community_cards = [str(c) for c in self.table.dealer.tableCards.cards]
        else:
            community_cards = [str(c) for c in self.table.dealer.tableCards]

        # 2. Build the list of all players at the table and their statuses
        players_info = []
        for p in self.active_players:
            # Show actual cards ONLY if this is the viewer OR if we reached Showdown
            if p.username == viewer_player.username or self.roundStage == RoundStage.SHOWDOWN:
                hand_str = [str(c) for c in p.currentHand]
            else:
                hand_str = ["Hidden" for _ in p.currentHand]

            players_info.append({
                "username": p.username,
                "balance": p.currentBalance,
                "is_folded": p.isFolded,
                "is_turn": p.isPlayerTurn,
                "hand": hand_str
            })

        return {
            "status": "ok",
            "type": "game_state",
            "table_name": self.table.tableName,
            "stage": self.roundStage.value,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_turn": self.get_current_player().username,
            "community_cards": community_cards,
            "players": players_info
        }

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
        self.table.dealer.tableCards = []
