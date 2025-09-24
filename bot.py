from game_state import GameState
from custom_types import Move
from mtcs_engine import MCTS


class Bot:
    def __init__(self):
        self.mcts = MCTS(time_limit=1.0, iter_limit=1000)

    def get_move(self, game_state: GameState) -> Move | None:
        return self.mcts.search(game_state)