import copy
from typing import List, Set, Tuple
import logging

from custom_types import Move, PlayerType, PlayerTileClaim, Board

logger = logging.getLogger(__name__)
    
class GameState:
    def __init__(self, board=None, player_to_move=PlayerType.BLACK):
        self.board = board or Board()
        self.player = player_to_move

    def copy(self):
        return GameState(copy.deepcopy(self.board), self.player)
    
    def is_inside_board(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def opponent(self, player: PlayerType | None = None) -> PlayerType:
        if player is None: 
            player = self.player
        return PlayerType.WHITE if player == PlayerType.BLACK else PlayerType.BLACK

    def try_generate_moves(self) -> List[Move]:
        player = self.player
        captures: List[Move] = []
        moves: List[Move] = []
        
        for row, col, _ in self.board.iter_player_tiles(player):
            piece = self.board.tiles[row][col]
            if not piece.is_set or piece.color != player: 
                continue
            
            moves.extend(self._directional_moves(row,col))
            caps = self._try_capture(row,col)
            if caps:
                captures.extend(caps)
        
        if captures:
            return captures
        
        return moves
        
    def apply_move(self, move: Move):
        board = self.board.tiles
        row,col = move[0]
        piece = board[row][col]
        board[row][col] = PlayerTileClaim()
        
        for (next_row,next_col) in move[1:]:
            if abs(next_row - row) == 2:
                cap_row = (row + next_row)//2
                cap_col = (col + next_col)//2
                logger.debug(f"capture at {(cap_row,cap_col)} by move {(row,col)} -> {(next_row,next_col)}")
                board[cap_row][cap_col] = PlayerTileClaim()
            row,col = next_row,next_col
            
        piece = self._check_promotion(row, piece)
        piece.is_set = True
        board[row][col] = piece
        
        self.player = self.opponent()
        logger.debug(f"next to move: {self.player}")
        
    def winner(self) -> PlayerType | None:
        black_left = self._remaining_tiles(PlayerType.BLACK)
        white_left = self._remaining_tiles(PlayerType.WHITE)
        
        if black_left == 0: 
            return PlayerType.WHITE
        
        if white_left == 0: 
            return PlayerType.BLACK
        
        if not self.try_generate_moves():
            win = self.opponent(self.player)
            return win
        
        return None
    
    def _dfs(self, board: Board, row: int, col: int, path: List[Tuple[int,int]], captured: Set[Tuple[int,int]], result_possible_moves: List[Move]):
        any_capture = False
        piece = board.tiles[row][col]
        directions = self._get_directions(piece)
        
        for dir_row,dir_col in directions:
            row_1,col_1 = row + dir_row, col + dir_col
            row_2,col_2 = row + 2*dir_row, col + 2*dir_col
            
            if not self.is_inside_board(row_2,col_2) or not self.is_inside_board(row_1,col_1):
                continue
            
            target_piece = board.tiles[row_1][col_1]
            landing = board.tiles[row_2][col_2]
            
            if not piece.is_set or piece.color is None:
                continue
            if not self._can_be_captured(row_1,col_1,captured,target_piece,landing,piece.color):
                continue
            
            any_capture = True
            new_board = copy.deepcopy(board)
            new_board.tiles[row_2][col_2] = new_board.tiles[row][col]
            new_board.tiles[row][col] = PlayerTileClaim()
            new_board.tiles[row_1][col_1] = PlayerTileClaim()
            new_captured = captured | {(row_1,col_1)}
            self._dfs(new_board, row_2,col_2, path+[(row_2,col_2)], new_captured, result_possible_moves)
                
        if not any_capture:
            result_possible_moves.append(path)
            
    def _can_be_captured(self, row: int, col: int, captured: Set[Tuple[int,int]], target_piece: PlayerTileClaim, landing: PlayerTileClaim, attacker_color: PlayerType) -> bool:
        return (target_piece.is_set
                and target_piece.color != attacker_color
                and not landing.is_set 
                and (row,col) not in captured
        )
                    
    def _get_directions(self, piece: PlayerTileClaim) -> List[Tuple[int,int]]:
        if piece.is_king:
            return [(1,-1),(1,1),(-1,-1),(-1,1)]
        if piece.color == PlayerType.BLACK:
            return [(1,-1),(1,1)]
        return [(-1,-1),(-1,1)]

    def _directional_moves(self, row: int, col: int) -> List[Move]:
        piece = self.board.tiles[row][col]
        possible_moves: List[Move] = []
        directions = self._get_directions(piece)
            
        for dir_row, dir_col in directions:
            next_row,next_col = row + dir_row, col + dir_col
            
            if not self.is_inside_board(next_row,next_col):
                continue
            
            target_piece = self.board.tiles[next_row][next_col]
            if not target_piece.is_set:
                possible_moves.append([(row,col),(next_row,next_col)])
                
        return possible_moves

    def _try_capture(self, row: int, col: int) -> List[Move]:
        possible_moves: List[Move] = []
        self._dfs(self.board, row,col, [(row,col)], set(), possible_moves)
        filtered_moves = [m for m in possible_moves if len(m)>=2]
        return filtered_moves
    
        
    def _check_promotion(self, row: int, piece: PlayerTileClaim) -> PlayerTileClaim:
        if piece.color == PlayerType.BLACK and row == 7:
            return PlayerTileClaim(is_set=True, color=PlayerType.BLACK, is_king=True)
        if piece.color == PlayerType.WHITE and row == 0:
            return PlayerTileClaim(is_set=True, color=PlayerType.WHITE, is_king=True)
        return piece
    
    def _remaining_tiles(self, player: PlayerType) -> int:
        return sum(1 for _, _, tile in self.board.iter_tiles() if tile.is_set and tile.color == player)