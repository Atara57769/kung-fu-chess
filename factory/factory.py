from typing import Optional
from models.pieces import Piece
from models.cell import Cell
from constants import EMPTY_TOKEN, VALID_COLORS, VALID_PIECES

class PieceFactory:
    @staticmethod
    def from_text(token: str, cell: Cell = None) -> Optional[Piece]:
        if token == EMPTY_TOKEN:
            return None
        if len(token) < 2:
            return None
        color = token[0]
        kind = token[1]
        
        if color in VALID_COLORS and kind in VALID_PIECES:
            return Piece(color, kind, cell)
        return None

    @staticmethod
    def to_text(piece: Optional[Piece]) -> str:
        """Gets a piece and returns its token."""
        if piece is None:
            return EMPTY_TOKEN
        return piece.color + piece.kind
