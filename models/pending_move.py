from dataclasses import dataclass
from models.cell import Cell
from models.pieces import Piece

@dataclass
class PendingMove:
    from_pos: Cell
    to_pos: Cell
    piece: Piece
    arrival: int
