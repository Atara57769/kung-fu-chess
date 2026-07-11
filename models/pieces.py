from dataclasses import dataclass
from models.cell import Cell

@dataclass
class Piece:
    color: str  # "w" / "b"
    kind: str   # "K" / "Q" / "R" / "B" / "N" / "P"
    cell: Cell = None




