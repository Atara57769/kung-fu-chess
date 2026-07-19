from dataclasses import dataclass
from models.cell import Cell

@dataclass
class PieceMoved:
    from_pos: Cell
    to_pos: Cell

from models.color import Color
from models.piece_type import PieceType

@dataclass
class PieceCaptured:
    attacker_color: Color
    victim_color: Color
    victim_kind: PieceType

@dataclass
class ScoreChanged:
    white_score: int
    black_score: int

from typing import List, Tuple

@dataclass
class GameStarted:
    initial_pieces: List[Tuple[Color, PieceType]]

@dataclass
class GameEnded:
    winner: str
