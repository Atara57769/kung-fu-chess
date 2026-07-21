from dataclasses import dataclass, field
from typing import List, Optional
from shared.models.board import Board
from shared.models.pending_move import PendingMove
from shared.models.jump import Jump
from shared.models.pieces import Piece

@dataclass
class GameState:
    board: Board
    selected_piece: Optional[Piece] = None
    black_selected_piece: Optional[Piece] = None
    game_over: bool = False
    clock: int = 0
    pending_moves: List[PendingMove] = field(default_factory=list)
    jumps: List[Jump] = field(default_factory=list)
