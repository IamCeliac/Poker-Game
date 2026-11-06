from game_files.player import Player
from dealer import Dealer

class Table:

    players: list[Player]
    def __init__(self, tableName):
        self.table_id = tableName
        self.players = []
        self.dealer = Dealer()
        self.prizePot = 0

    def add_player(self, player):
        if len(self.players) >= 5:
            raise ValueError("Maximum of 5 players already at the table.")
        if isinstance(player, Player):
            self.players.append(player)
        else:
            raise ValueError("Only instances of Player can be added to the table.")

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
        else:
            raise ValueError("Player not found at the table.")

    
        