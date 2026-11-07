from game_files.round import Round
from game_files.table import Table
class Game:
    
    openTables: list[Table] = []
    
    def start_game(self,table:Table):
        return Round(table)

    def end_game(self,round:Round):
        round.reset_game()

    @staticmethod
    def GetTableByName(tableName) -> Table:
        for currentTable in Game.openTables:
            if tableName == currentTable.tableName:
                return currentTable
            

        