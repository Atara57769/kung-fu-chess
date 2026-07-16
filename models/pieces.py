from dataclasses import dataclass
from typing import Optional
from enum import Enum
from models.cell import Cell
from models.piece_type import PieceType
from models.color import Color
from constants import EMPTY_TOKEN, TOKEN_LENGTH, COLOR_INDEX, KIND_INDEX

class PieceStatus(Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"

@dataclass
class Piece:
    color: Color
    kind: PieceType
    cell: Cell = None
    cooldown_until: int = 0
    status: PieceStatus = PieceStatus.IDLE


    @classmethod
    def from_text(cls, token: str, cell: Cell = None) -> Optional['Piece']:
        if token == EMPTY_TOKEN:
            return None
        if len(token) < TOKEN_LENGTH:
            return None
        color = token[COLOR_INDEX]
        kind = token[KIND_INDEX]
        
        if color in Color._value2member_map_ and kind in PieceType._value2member_map_:
            return cls(Color(color), PieceType(kind), cell)
        return None

    @classmethod
    def to_text(cls, piece: Optional['Piece']) -> str:
        """Gets a piece and returns its token."""
        if piece is None:
            return EMPTY_TOKEN
        return piece.color + piece.kind
