CELL_SIZE = 100
EMPTY_TOKEN = '.'
from models.color import Color

DURATION = 1000
COOLDOWN_DURATION = 1000
COOLDOWN_JUMP = 700
COOLDOWN_MOVE = 1500
TOKEN_LENGTH = 2
COLOR_INDEX = 0
KIND_INDEX = 1

PAWN_DIRECTION_WHITE = -1
PAWN_DIRECTION_BLACK = 1
PAWN_DIRECTIONS = {
    Color.WHITE: PAWN_DIRECTION_WHITE,
    Color.BLACK: PAWN_DIRECTION_BLACK,
}

DEFAULT_BOARD_LAYOUT = [
    "bR bN bB bQ bK bB bN bR",
    "bP bP bP bP bP bP bP bP",
    ".  .  .  .  .  .  .  .",
    ".  .  .  .  .  .  .  .",
    ".  .  .  .  .  .  .  .",
    ".  .  .  .  .  .  .  .",
    "wP wP wP wP wP wP wP wP",
    "wR wN wB wQ wK wB wN wR"
]

from models.piece_type import PieceType
PIECE_POINTS = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 3,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.KING: 0
}