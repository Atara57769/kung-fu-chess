from dataclasses import dataclass
from models.cell import Cell

@dataclass
class Piece:
    color: str  
    kind: str   
    cell: Cell = None




