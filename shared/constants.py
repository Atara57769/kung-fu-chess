CELL_SIZE = 100
EMPTY_TOKEN = '.'
from shared.models.color import Color

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

from shared.models.piece_type import PieceType
PIECE_POINTS = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 3,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.KING: 0
}

# Network Server Configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8765
HEARTBEAT_INTERVAL = 5.0
HEARTBEAT_TIMEOUT = 10.0
DISCONNECT_COUNTDOWN = 20

ROOM_STATUS_WAITING = "waiting"
ROOM_STATUS_ACTIVE = "active"
ROOM_STATUS_ENDED = "ended"

MATCHMAKING_STATUS_WAITING = "waiting"
MATCHMAKING_STATUS_IDLE = "idle"
MATCHMAKING_STATUS_TIMEOUT = "timeout"

COLOR_NAME_WHITE = "white"
COLOR_NAME_BLACK = "black"
GAME_RESULT_DRAW = "draw"

MSG_UNAUTHORIZED = "Unauthorized client."
MSG_ROOM_ALREADY_EXISTS = "Room already exists."
MSG_ROOM_NOT_FOUND = "Room not found."



