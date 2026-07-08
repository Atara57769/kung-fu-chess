from dataclasses import dataclass
from models.coordinate import Coordinate
from models.pieces import Piece

@dataclass
class PendingMove:
    from_pos: Coordinate
    to_pos: Coordinate
    piece: Piece
    arrival: int
