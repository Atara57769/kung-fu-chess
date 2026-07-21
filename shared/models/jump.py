from dataclasses import dataclass
from typing import Tuple
from shared.models.pieces import Piece

@dataclass
class Jump:
    cell: Tuple[int, int]
    start: int
    end: int
    piece: Piece
