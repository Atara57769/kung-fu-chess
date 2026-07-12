from dataclasses import dataclass
from typing import Optional
from models.cell import Cell
from constants import EMPTY_TOKEN, VALID_COLORS, VALID_PIECES, TOKEN_LENGTH, COLOR_INDEX, KIND_INDEX

@dataclass
class Piece:
    color: str  
    kind: str   
    cell: Cell = None
    cooldown_until: int = 0

    @classmethod
    def from_text(cls, token: str, cell: Cell = None) -> Optional['Piece']:
        if token == EMPTY_TOKEN:
            return None
        if len(token) < TOKEN_LENGTH:
            return None
        color = token[COLOR_INDEX]
        kind = token[KIND_INDEX]
        
        if color in VALID_COLORS and kind in VALID_PIECES:
            return cls(color, kind, cell)
        return None

    @classmethod
    def to_text(cls, piece: Optional['Piece']) -> str:
        """Gets a piece and returns its token."""
        if piece is None:
            return EMPTY_TOKEN
        return piece.color + piece.kind
