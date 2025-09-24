from __future__ import annotations
import random
import math
import time
import logging
from typing import List, NamedTuple
from custom_types import PlayerType, Move
from game_state import GameState

logger = logging.getLogger(__name__)


class Choice(NamedTuple):
    uct: float
    node: MCTSNode  
    
    
class MCTSNode:
    _MAX_DEPTH = 200 # arbitrary depth limit
    _C_PARAM = math.sqrt(2) # UCT constant
    
    def __init__(self, state: GameState, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children: List[MCTSNode] = []
        self.visits: int = 0
        self.wins: float = 0.0
        self.available_moves: List[Move] = state.try_generate_moves()

    def select(self):
        choices: List[Choice] = []
        
        for child in self.children:
            if child.visits==0:
                uct = float('inf')
            else:
                uct = self._upper_confidence_tree(child)
            
            choice = Choice(uct,child)
            choices.append(choice)
            
        # return the child with the highest upper confidence bound
        return max(choices, key=lambda choice: choice.uct).node
    
    def expand(self):
        random_index = random.randrange(len(self.available_moves))
        move = self.available_moves.pop(random_index)
        
        next_state = self.state.copy()
        next_state.apply_move(move)
        
        child = MCTSNode(next_state, parent=self, move=move)
        self.children.append(child)
        return child

    
    def is_fully_expanded(self):
        return len(self.available_moves) == 0

    def simulate(self):
        current_state = self.state.copy()
        depth = 0
        
        while True:
            # there is a winner
            winner = current_state.winner()
            if winner is not None:
                return winner
            
            # there are no moves
            moves = current_state.try_generate_moves()
            if not moves:
                return current_state.opponent()
            
            # apply a move
            move = self._apply_rollout_policy(moves)
            current_state.apply_move(move)
            depth += 1
            if depth > self._MAX_DEPTH:
                return None
            
    def _upper_confidence_tree(self, child: MCTSNode) -> float:
        # Upper Confidence Bounds applied for Trees (UCT) introduced by Kocsis and Szepesvári (2006) 
        log_visits = math.log(self.visits)
        average_actions_result = child.wins/child.visits
        return average_actions_result + self._C_PARAM * math.sqrt(log_visits/child.visits)   
    
    def _apply_rollout_policy(self, possible_moves: List[Move]):
        return random.choice(possible_moves)  
    

class MCTS:
    _ITER_LIMIT: int = 10000 # arbitrary iteration limit
    _TIME_LIMIT: float = 1.0 # arbitrary time limit
    
    def __init__(self, time_limit, iter_limit):
        self.time_limit = time_limit or self._TIME_LIMIT
        self.iter_limit = iter_limit or self._ITER_LIMIT

    def search(self, initial_state: GameState):
        logger.info(f"MCTS search start: player={initial_state.player}, time_limit={self.time_limit}, iter_limit={self.iter_limit}")
        
        root = MCTSNode(initial_state.copy())
        start_time = time.time()
        iterations = 0
        
        while True:
            if self._limits_reached(start_time, iterations):
                break
            
            node = root
            while node.is_fully_expanded() and node.children:
                node = node.select()
                
            if not node.is_fully_expanded():
                node = node.expand()
                
            winner = node.simulate()
            self.backpropagate(node, winner)
            iterations += 1
            
        if not root.children:
            return None
            
        best = max(root.children, key=lambda child: child.visits)
        logger.info(f"MCTS search end: iterations={iterations}, best_move={best.move if best else None}")
        return best.move if best else None

    def backpropagate(self, node: MCTSNode, winner: PlayerType | None):
        current_node = node
        while current_node is not None:
            current_node.visits += 1
            player = current_node.state.player
            mover = current_node.state.opponent(player)
            
            if winner is None:
                current_node.wins += 0.5
            elif winner == mover:   
                current_node.wins += 1
                                    
            current_node = current_node.parent
            
    
    def _limits_reached(self, start_time: float, iterations: int):
        if self.iter_limit and iterations >= self.iter_limit:
            return True
        if time.time() - start_time > self.time_limit:
            return True
        return False