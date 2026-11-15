from game_files.player import Player
from game_files.dealer import Dealer

class Table:

    players: list[Player]
    
    def __init__(self, tableName,creatorUsername=""):
        self.tableName = tableName
        self.creator = creatorUsername
        self.players = []
        self.dealer = Dealer()
        self.prizePot = 0

    def add_player(self, player):
        if len(self.players) >= 5:
            raise ValueError("Maximum of 5 players already at the table.")
        if isinstance(player, Player):
            if player not in self.players:
                self.players.append(player)
        else:
            raise ValueError("Only instances of Player can be added to the table.")

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)

            if len(self.players) == 0:
                from game_files.game import Game
                if self in Game.openTables:
                    Game.openTables.remove(self)
                    print(f"[AUTO-DELETE] Table '{self.tableName}' had 0 players and was deleted.")
        else:
            raise ValueError("Player not found at the table.")

    
        