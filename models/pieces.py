from dataclasses import dataclass
from models.cell import Cell

@dataclass
class Piece:
    color: str  # "w" / "b"
    kind: str   # "K" / "Q" / "R" / "B" / "N" / "P"
    cell: Cell = None


class PieceFactory:
    @staticmethod
    def get_piece(token: str, cell: Cell = None) -> Piece:
        from constants import EMPTY_TOKEN, VALID_COLORS, VALID_PIECES
        if token == EMPTY_TOKEN:
            return None
        if len(token) < 2:
            return None
        color = token[0]
        kind = token[1]
        
        if color in VALID_COLORS and kind in VALID_PIECES:
            return Piece(color, kind, cell)
        return None



