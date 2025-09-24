import tkinter as tk
import logging

from custom_types import PlayerType
from game_state import GameState
from ui import CheckersUI


class GameLoop:
    def __init__(self, human_player: PlayerType):
        self.root = tk.Tk()
        self.root.title("Checkers with MCTS")
        self.ui = CheckersUI(self.root, GameState(), human_player)
        
    def run(self):
        self.root.mainloop()
        
    def stop(self):
        self.root.quit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    loop = GameLoop(human_player=PlayerType.WHITE)
    loop.run()