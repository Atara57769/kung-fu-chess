import sys
from typing import Optional
from models.pieces import Piece
from constants import EMPTY_TOKEN

def print_piece(piece: Optional[Piece]) -> str:
    """Gets a piece and returns its token."""
    if piece is None:
        return EMPTY_TOKEN
    return piece.color + piece.kind

def print_board(board, stdout=sys.stdout) -> None:
    """Prints the board in canonical space-separated format using print_piece."""
    for y in range(board.height):
        row_tokens = []
        for x in range(board.width):
            piece = board.get_piece_at(y, x)
            row_tokens.append(print_piece(piece))
        print(" ".join(row_tokens), file=stdout)
