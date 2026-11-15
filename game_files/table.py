from game_files.player import Player
from game_files.dealer import Dealer

class Table:

    players: list[Player]
    
    def __init__(self, tableName,creatorUsername="", min_bet=20):
        if min_bet < 10 or min_bet > 1000:
            raise ValueError("Minimum bet must be between 10 and 1000.")
        if min_bet % 2 != 0:
            raise ValueError("Minimum bet must be an even number!")
        self.tableName = tableName
        self.creator = creatorUsername
        self.min_bet = int(min_bet)
        self.dealer_button_index = 0
        self.players = []
        self.dealer = Dealer()
        self.prizePot = 0

    def add_player(self, player):
        if len(self.players) >= 5:
            raise ValueError("Maximum of 5 players already at the table.")
        if not isinstance(player, Player):
            raise ValueError("Only instances of Player can be added to the table.")
        if player.currentBalance < self.min_bet * 2:
            raise ValueError(
                f"Insufficient balance. You need at least {self.min_bet * 2} chips (2x min bet) to join this table."
            )
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player: Player):
        if player in self.players:
            self.players.remove(player)

            if len(self.players) == 0:
                from game_files.game import Game
                if self in Game.openTables:
                    Game.openTables.remove(self)
                    print(f"[AUTO-DELETE] Table '{self.tableName}' had 0 players and was deleted.")
        else:
            raise ValueError("Player not found at the table.")

    
        