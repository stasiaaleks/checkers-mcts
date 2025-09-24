import tkinter as tk
import logging
from custom_types import PlayerType
from game_state import GameState
from bot import Bot

logger = logging.getLogger(__name__)

class CheckersUI:
    selected = None
    legal_destinations = set()
    bot = Bot()
    human_last_move = None
    bot_last_move = None
    
    CELL_SIZE = 50
    
    def __init__(self, root, state: GameState, human_player=PlayerType.WHITE):
        self.root = root
        self.state = state
        self.canvas = tk.Canvas(root, width=400, height=400)
        self.canvas.pack()
        self.human_player = human_player
        self.canvas.bind("<Button-1>", self.on_click)
   
        self.draw_board()
        
        if self.state.player != self.human_player:
            self.root.after(200, self.show_bot_move)

    def draw_board(self):
        self.canvas.delete("all")
        
        # collect highlighted positions: current selection and last move destinations
        highlights = set()
        if self.selected:
            highlights.add(self.selected)
        if self.human_last_move:
            highlights.add(self.human_last_move[-1])
        if self.bot_last_move:
            highlights.add(self.bot_last_move[-1])
        
        for row, col, _ in self.state.board.iter_tiles():
            x0,y0 = col*self.CELL_SIZE, row*self.CELL_SIZE
            x1,y1 = x0+self.CELL_SIZE, y0+self.CELL_SIZE
            color = "#EEE" if (row+col)%2==0 else "#666"
            self.canvas.create_rectangle(x0,y0,x1,y1, fill=color)

            if (row, col) in self.legal_destinations:
                self.canvas.create_rectangle(x0+3,y0+3,x1-3,y1-3, outline="#ff0", width=3)
            piece = self.state.board.tiles[row][col]
            if not piece.is_set:
                continue
                
            
            fill = "white" if piece.color==PlayerType.WHITE else "black"
            if (row,col) in highlights:
                self.canvas.create_oval(x0+5,y0+5,x1-5,y1-5, fill=fill, outline="red", width=3)
            else:
                self.canvas.create_oval(x0+5,y0+5,x1-5,y1-5, fill=fill)
            if piece.is_king:
                self.canvas.create_text((x0+x1)//2,(y0+y1)//2, text="K", fill="red")

    def on_click(self, event):
        if self.state.player != self.human_player:
            return
        
        col = event.x // self.CELL_SIZE
        row = event.y // self.CELL_SIZE

        if not self.state.is_inside_board(row,col):
            self.selected = None
            self.legal_destinations = set()
            return
        
        tile = self.state.board.tiles[row][col]
        if self.selected is None:
            if tile.is_set and tile.color == self.human_player:
                self.selected = (row,col)
                logger.info(f"human selected piece: {self.selected}")
                moves = self.state.try_generate_moves()
                self.legal_destinations = {
                    m[-1] for m in moves if len(m) >= 2 and m[0] == self.selected
                }
                self.draw_board()
        else:
            legal_moves = self.state.try_generate_moves()
            logger.debug(f"human attempt to move from {self.selected}, legal_moves={len(legal_moves)}")
            for move in legal_moves:
                if len(move) < 2 or move[0] != self.selected:
                    continue
                
                if move[-1] == (row, col):
                    logger.info(f"human move chosen: {move}")
                    self.state.apply_move(move)
                    self.human_last_move = move
                    self.selected = None
                    self.legal_destinations = set()
                    self.draw_board()
                    self.root.after(500, self.show_bot_move)
                    return
            self.selected = None
            self.draw_board()

    def show_bot_move(self):
        if self.state.player != self.human_player:
            logger.info("bot is thinking...")
            move = self.bot.get_move(self.state)
            
            if move:
                logger.info(f"bot move: {move}")
                self.bot_last_move = move
                self.state.apply_move(move)
                
            self.draw_board()
            
        if self.state.winner():
            self.show_winner()

    def show_winner(self):
        winner = self.state.winner()
        logger.info(f"game finished, winner: {winner}")
        
        result_message = "DRAW" if winner is None else ("YOU WON!" if winner==self.human_player else "BOT WON!")
        self.canvas.create_text(200,200,text=result_message, fill="red", font=("Arial",24))