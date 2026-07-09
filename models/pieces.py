from models.cell import Cell

class Piece:
    def __init__(self, color: str, kind: str, cell: Cell = None):
        self.color = color  # "w" / "b"
        self.kind = kind    # "K" / "Q" / "R" / "B" / "N" / "P"
        self.cell = cell


def get_piece(token, cell: Cell = None) -> Piece:
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
