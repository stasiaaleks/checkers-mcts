from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum


Coord = Tuple[int,int]
Move = List[Coord]


class PlayerType(Enum):
    WHITE = 'white'
    BLACK = 'black'

@dataclass
class PlayerTileClaim():
    is_set: bool = False
    color: PlayerType | None = None
    is_king: bool = False



class Board:
    tiles: List[List[PlayerTileClaim]]
    
    def __init__(self, board: List[List[PlayerTileClaim]] | None = None):
        self.tiles = board or self._generate_initial_board()
        
    def iter_coords(self):
        for row in range(8):
            for col in range(8):
                yield row, col

    def iter_tiles(self):
        for row, col in self.iter_coords():
            yield row, col, self.tiles[row][col]

    def iter_player_tiles(self, player: PlayerType):
        for row, col, tile in self.iter_tiles():
            if tile.is_set and tile.color == player:
                yield row, col, tile
        
    def _generate_initial_board(self) -> List[List[PlayerTileClaim]]:
        board = [[PlayerTileClaim() for _ in range(8)] for __ in range(8)]
        
        for row in range(3):
            board[row] = self._color_row(row, PlayerType.BLACK)
                    
        for row in range(5,8):
            board[row] = self._color_row(row, PlayerType.WHITE)
        return board
    
    def _color_row(self, row: int, color: PlayerType) -> List[PlayerTileClaim]:
        return [PlayerTileClaim(is_set=True, color=color) if (row + col) % 2 == 1 else PlayerTileClaim() for col in range(8)]