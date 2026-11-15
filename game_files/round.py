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
    FINISHED = "Finished"

class Round:
    
    def __init__(self, table: Table):
        self.roundStage = RoundStage.PRE_FLOP
        self.table = table
        self.current_bet = 0
        self.pot = 0
        self.active_players = [player for player in table.players]
        self.currentPlayerTurnIndex = 0
        self.playersActedThisStreet = set()

    def start_round(self):
        if len(self.active_players) < 2:
            raise ValueError("Not enough players to start the round.")
        self.table.dealer.ShuffleDeck()
        self.playersActedThisStreet.clear()
        for player in self.active_players:
            player.isPlayerTurn = False
            player.currentStreetbet = 0
            player.currentHand = [self.table.dealer.DealCard(), self.table.dealer.DealCard()]

        self.currentPlayerTurnIndex = 0
        self.active_players[0].isPlayerTurn = True

    def advance_stage(self):

        self.current_bet = 0

        if self.roundStage == RoundStage.PRE_FLOP:
            self.roundStage = RoundStage.FLOP
            for _ in range(3):
                self.table.dealer.DealTableCards()
            self.reset_active_bets()
        elif self.roundStage == RoundStage.FLOP:
            self.roundStage = RoundStage.TURN
            self.table.dealer.DealTableCards()
            self.reset_active_bets()
        elif self.roundStage == RoundStage.TURN:
            self.roundStage = RoundStage.RIVER
            self.table.dealer.DealTableCards()
            self.reset_active_bets()
        elif self.roundStage == RoundStage.RIVER:
            self.roundStage = RoundStage.SHOWDOWN
            self.reset_active_bets()
        else:
            raise ValueError("Round has already reached the SHOWDOWN stage.")


    def reset_active_bets(self):
        self.current_bet = 0
        self.playersActedThisStreet.clear()
        for player in self.active_players:
            player.currentStreetbet = 0

    def get_current_player(self):
        if self.roundStage == RoundStage.FINISHED:
            return None
        if not self.active_players:
            raise ValueError("No active players left in the round.")
        return self.active_players[self.currentPlayerTurnIndex]

    def handle_player_action(self, player: Player, action, amount=0):
        """Processes a player's move, adds chips to the pot, and moves to the next turn."""
        if not player.isPlayerTurn:
            raise ValueError(f"It is not {player.username}'s turn!")

        owed = self.current_bet - player.currentStreetbet

        if action == "check":
            if owed > 0:
                raise ValueError(f"Cannot check. You must call {owed}, raise, or fold.")
            self.playersActedThisStreet.add(player.username)

        elif action == "call":
            if owed <= 0:
                raise ValueError("Nothing to call. You can check or bet.")
            if owed >= player.currentStreetbet:
                chips = player.AllIn()
            else:
                chips = player.PlaceBet(owed)
            self.pot += chips
            self.playersActedThisStreet.add(player.username)

        elif action == "bet":
            if self.current_bet > 0:
                raise ValueError("A bet has already been placed. Use raise instead.")
            chips = player.PlaceBet(amount)
            self.current_bet = player.currentStreetbet
            self.pot += chips
            self.playersActedThisStreet = {player.username}

        elif action == "raise":
            if self.current_bet == 0:
                raise ValueError("No bet to raise. Use 'bet' instead.")
            if amount <= self.current_bet:
                raise ValueError(f"Raise must be greater than current bet ({self.current_bet}).")
            to_add = amount - player.currentStreetBet
            chips = player.PlaceBet(to_add)
            self.current_bet = player.currentStreetBet
            self.pot += chips
            self.playersActedThisStreet = {player.username}

        
        elif action == "all_in":
            chips = player.AllIn()
            self.pot += chips
            if player.currentStreetbet > self.current_bet:
                self.current_bet = player.currentStreetbet
                self.playersActedThisStreet = {player.username}
            else:
                self.playersActedThisStreet.add(player.username)
            print(f"{player.username} is All in with {chips}. Total pot: {self.pot}")
        
        elif action == "fold":
            player.Fold()
            print(f"{player.username} folded.")

        # Automatically pass the turn to the next active player!
        self.next_player_turn()
        

    def next_player_turn(self):
        # 1. Turn off current player's turn
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = False

        # 2. Check how many players haven't folded yet
        unfolded_players = [p for p in self.active_players if not p.isFolded]
        if len(unfolded_players) <= 1:
            winner = unfolded_players[0]
            print(f"{winner.username} wins the pot of {self.pot}!")
            winner.currentBalance += self.pot

            for p in self.active_players:
                p.isPlayerTurn = False
                p.isFolded = False
                p.currentHand = []
                User.UpdateUserBalance(p.username,p.currentBalance)

            self.table.dealer.tableCards = []
            self.roundStage = RoundStage.FINISHED
            return

        can_act = [p for p in unfolded_players if p.currentBalance > 0]

        if len(can_act) == 0 or (
            len(can_act) == 1
            and can_act[0].username in self.playersActedThisStreet
            and can_act[0].currentStreetbet >= self.current_bet
        ):
            while self.roundStage != RoundStage.SHOWDOWN:
                self.advance_stage()
            self.resolve_showdown()
            return

        all_matched = all(
            p.username in self.players_acted_this_street and p.currentStreetBet == self.current_bet
            for p in can_act
        )

        if all_matched:
            self.advance_stage()
            if self.roundStage == RoundStage.SHOWDOWN:
                self.resolve_showdown()
                return
            for idx, p in enumerate(self.active_players):
                if not p.isFolded and p.currentBalance > 0:
                    self.currentPlayerTurnIndex = idx
                    p.isPlayerTurn = True
                    return
        
        # 3. Loop to the next player until we find one who hasn't folded
        while True:
            self.currentPlayerTurnIndex = (self.currentPlayerTurnIndex + 1) % len(self.active_players)
            next_player = self.active_players[self.currentPlayerTurnIndex]
            if not next_player.isFolded and next_player.currentBalance >0:
                next_player.isPlayerTurn = True
                break

    def resolve_showdown(self):
        unfolded_players = [p for p in self.active_players if not p.isFolded]
        
        player_scores = {
            p: self.table.dealer.get_best_hand(p.currentHand)
            for p in unfolded_players
        }
        best_score = max(player_scores.values())
        winners = [p for p, score in player_scores.items() if score == best_score]

        share = self.pot // len(winners)
        remainder = self.pot % len(winners)

        for idx, winner in enumerate(winners):
            payout = share + (remainder if idx == 0 else 0)
            winner.currentBalance += payout
            print(f"{winner.username} wins {payout} from the pot at Showdown!")

        for p in self.active_players:
            p.isPlayerTurn = False
            p.isFolded = False
            User.UpdateUserBalance(p.username, p.currentBalance)

        self.roundStage = RoundStage.FINISHED
    
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
            if p.username == viewer_player.username or self.roundStage in (RoundStage.SHOWDOWN,RoundStage.FINISHED):
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

        current_player = self.get_current_player()
        return {
            "status": "ok",
            "type": "game_state",
            "table_name": self.table.tableName,
            "stage": self.roundStage.value,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_turn": current_player.username if current_player else None,
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


    def end_round(self):
        self.roundStage = self.roundStage+1
