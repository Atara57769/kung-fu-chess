from dataclasses import dataclass, field
from typing import List, Optional
from models.board import Board
from models.pending_move import PendingMove
from models.jump import Jump
from models.pieces import Piece

@dataclass
class GameState:
    board: Board
    selected_piece: Optional[Piece] = None
    game_over: bool = False
    clock: int = 0
    pending_moves: List[PendingMove] = field(default_factory=list)
    jumps: List[Jump] = field(default_factory=list)
