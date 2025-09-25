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
            delta_row = next_row - row
            delta_col = next_col - col
          
            if abs(delta_row) > 1 and abs(delta_col) > 1:
                step_row = 1 if delta_row > 0 else -1
                step_col = 1 if delta_col > 0 else -1
                check_row = row + step_row
                check_col = col + step_col

                while check_row != next_row:
                    if board[check_row][check_col].is_set:
                        logger.debug(f"capture at {(check_row,check_col)} by move {(row,col)} -> {(next_row,next_col)}")
                        board[check_row][check_col] = PlayerTileClaim()
                        break

                    check_row += step_row
                    check_col += step_col
                    
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
    
    def _dfs(self, 
             board: Board, 
             row: int, col: int, 
             path: List[Tuple[int,int]], 
             captured: Set[Tuple[int,int]], 
             result_possible_moves: List[Move]):
        
        piece = board.tiles[row][col]
        if not piece.is_set or piece.color is None:
            return

        directions = self._get_directions(piece)

        has_capture = self._dfs_captures(
                board,
                row,
                col,
                directions,
                piece,
                path,
                captured,
                result_possible_moves,
                piece.is_king,
            )

        if not has_capture:
            result_possible_moves.append(path)

    def _dfs_captures(
        self,
        board: Board,
        row: int,
        col: int,
        directions: List[Tuple[int, int]],
        piece: PlayerTileClaim,
        path: List[Tuple[int, int]],
        captured: Set[Tuple[int, int]],
        result_possible_moves: List[Move],
        is_king: bool
    ) -> bool:
        found_capture = False

        for dir_row, dir_col in directions:
            step_row, step_col = row + dir_row, col + dir_col

            while self.is_inside_board(step_row, step_col):
                current_tile = board.tiles[step_row][step_col]
                if not current_tile.is_set:
                    if not is_king:
                        break
                    
                    step_row += dir_row
                    step_col += dir_col
                    continue

                if current_tile.color == piece.color or (step_row, step_col) in captured:
                    break

                landing_row, landing_col = step_row + dir_row, step_col + dir_col

                while self.is_inside_board(landing_row, landing_col):
                    landing_tile = board.tiles[landing_row][landing_col]
                    if landing_tile.is_set:
                        break

                    self._apply_capture(
                        board,
                        row,
                        col,
                        landing_row,
                        landing_col,
                        step_row,
                        step_col,
                        path,
                        captured,
                        result_possible_moves
                    )
                    found_capture = True
                    
                    if not is_king:
                        break
                    
                    landing_row += dir_row
                    landing_col += dir_col

                break

        return found_capture

    def _apply_capture(
        self,
        board: Board,
        origin_row: int,
        origin_col: int,
        landing_row: int,
        landing_col: int,
        capture_row: int,
        capture_col: int,
        path: List[Tuple[int, int]],
        captured: Set[Tuple[int, int]],
        result_possible_moves: List[Move],
    ):
        origin_tile = board.tiles[origin_row][origin_col]
        captured_tile = board.tiles[capture_row][capture_col]
        landing_original = board.tiles[landing_row][landing_col]

        board.tiles[origin_row][origin_col] = PlayerTileClaim()
        board.tiles[capture_row][capture_col] = PlayerTileClaim()

        moved_piece = PlayerTileClaim(is_set=True, color=origin_tile.color, is_king=origin_tile.is_king)
        moved_piece = self._check_promotion(landing_row, moved_piece)
        board.tiles[landing_row][landing_col] = moved_piece

        new_captured = captured | {(capture_row, capture_col)}
        self._dfs(board, landing_row, landing_col, path + [(landing_row, landing_col)], new_captured, result_possible_moves)

        board.tiles[landing_row][landing_col] = landing_original
        board.tiles[capture_row][capture_col] = captured_tile
        board.tiles[origin_row][origin_col] = origin_tile

    def _can_be_captured(self, row: int, 
                         col: int, 
                         captured: Set[Tuple[int,int]], 
                         target_piece: PlayerTileClaim, 
                         landing: PlayerTileClaim, 
                         attacker_color: PlayerType | None) -> bool:
        
        return (target_piece.is_set
                and target_piece.color != attacker_color
                and attacker_color is not None
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

            while self.is_inside_board(next_row,next_col):
                target_piece = self.board.tiles[next_row][next_col]
                if target_piece.is_set:
                    break
                possible_moves.append([(row,col),(next_row,next_col)])
                if not piece.is_king:
                    break
                next_row += dir_row
                next_col += dir_col
                 
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