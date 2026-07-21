import sys
from shared.models.pieces import Piece
from shared.models.cell import Cell

def print_board(board, stdout=sys.stdout) -> None:
    """Prints the board in canonical space-separated format using Piece.to_text."""
    for y in range(board.height):
        row_tokens = []
        for x in range(board.width):
            piece = board.get_piece_at(Cell(y, x))
            row_tokens.append(Piece.to_text(piece))
        print(" ".join(row_tokens), file=stdout)

