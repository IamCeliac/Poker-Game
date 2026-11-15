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

    hand_names = {
         0: "High Card",
         1: "One Pair",
         2: "Two Pair",
         3: "Three of a Kind",
         4: "Straight",
         5: "Flush",
         6: "Full House",
         7: "Four of a Kind",
         8: "Straight Flush"
     }
    
    def __init__(self, table: Table):
        self.roundStage = RoundStage.PRE_FLOP
        self.table = table
        self.current_bet = 0
        self.pot = 0
        self.active_players = [player for player in table.players]
        self.currentPlayerTurnIndex = 0
        self.playersActedThisStreet = set()
        self.winner_message = None

    def start_round(self):
        if len(self.active_players) < 2:
            raise ValueError("Not enough players to start the round.")

        required_chips = self.table.min_bet * 2
        for player in self.active_players:
            if player.currentBalance < required_chips:
                raise ValueError(
                    f"{player.username} only has {player.currentBalance} chips and needs {required_chips} (2x min bet) to play."
                )
        
        self.table.dealer.ResetDealer()
        self.playersActedThisStreet.clear()

        for player in self.active_players:
            player.isPlayerTurn = False
            player.currentStreetbet = 0
            player.currentHand = [self.table.dealer.DealCard(), self.table.dealer.DealCard()]


        num_players = len(self.active_players)
        sb_index = self.table.dealer_button_index % num_players
        bb_index = (sb_index +1) % num_players
        first_turn_index = (bb_index + 1) % num_players
        self.table.dealer_button_index = (self.table.dealer_button_index + 1) % num_players

        small_blind = self.table.min_bet // 2
        big_blind = self.table.min_bet

        sb_player = self.active_players[sb_index]
        bb_player = self.active_players[bb_index]

        sb_player.currentBalance -= small_blind
        sb_player.currentStreetbet = small_blind

        bb_player.currentBalance -= big_blind
        bb_player.currentStreetbet = big_blind

        self.pot = small_blind + big_blind
        self.current_bet = big_blind

        self.currentPlayerTurnIndex = first_turn_index
        self.active_players[self.currentPlayerTurnIndex].isPlayerTurn = True

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
            if owed >= player.currentBalance:
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
            to_add = amount - player.currentStreetbet
            chips = player.PlaceBet(to_add)
            self.current_bet = player.currentStreetbet
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
            self.winner_message = f"{winner.username} wins the pot of {self.pot} (everyone else folded)!"
            print(self.winner_message)
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
            p.username in self.playersActedThisStreet and p.currentStreetbet == self.current_bet
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
        winning_hand_name = self.hand_names[best_score[0]]
        winners = [p for p, score in player_scores.items() if score == best_score]
        winner_names = []

        share = self.pot // len(winners)
        remainder = self.pot % len(winners)

        for idx, winner in enumerate(winners):
            payout = share + (remainder if idx == 0 else 0)
            winner.currentBalance += payout
            winner_names.append(f"{winner.username} (+{payout})")

        self.winner_message =(
            f"SHOWDOWN: {','.join(winner_names)} won the pot of {self.pot} with {winning_hand_name}!"
        )
        print(self.winner_message)

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
            "players": players_info,
            "winner_message": self.winner_message
        }

    def remove_folded_players(self):
        self.active_players = [player for player in self.active_players if not player.isFolded]
        if self.currentPlayerTurnIndex >= len(self.active_players):
            self.currentPlayerTurnIndex = 0

    def handle_player_disconnect(self,player: Player):
        if player not in self.active_players or player.isFolded or self.roundStage == RoundStage.FINISHED:
            return

        if player.isPlayerTurn:
            self.handle_player_action(player,"fold")
            return

        player.Fold()
        unfolded_players = [p for p in self.active_players if not p.isFolded]
        if len(unfolded_players) <= 1:
            winner = unfolded_players[0]
            self.winner_message = f"{winner.username} wins the pot of {self.pot} (everyone else folded)!"
            print(self.winner_message)
            winner.currentBalance += self.pot
            for p in self.active_players:
                p.isPlayerTurn = False
                p.isFolded = False
                p.currentHand = []
                User.UpdateUserBalance(p.username,p.currentBalance)
            self.table.dealer.tableCards = []
            self.roundStage = RoundStage.FINISHED

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
