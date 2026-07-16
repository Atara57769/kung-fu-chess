CELL_SIZE = 100
EMPTY_TOKEN = '.'

COLOR_WHITE = 'w'
COLOR_BLACK = 'b'

VALID_COLORS = {COLOR_WHITE, COLOR_BLACK}

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
    COLOR_WHITE: PAWN_DIRECTION_WHITE,
    COLOR_BLACK: PAWN_DIRECTION_BLACK,
}

# Standard starting board layout for Kung-Fu Chess
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