from round import Round
from table import Table
class Game:
    def __init__(self, table: Table):
        self.round = Round(table)

    def start_game(self):
        self.round.start_round()

    def end_game(self):
        self.round.reset_game()
        