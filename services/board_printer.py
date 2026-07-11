import sys
from factory import PieceFactory

def print_board(board, stdout=sys.stdout) -> None:
    """Prints the board in canonical space-separated format using PieceFactory.to_text."""
    for y in range(board.height):
        row_tokens = []
        for x in range(board.width):
            piece = board.get_piece_at(y, x)
            row_tokens.append(PieceFactory.to_text(piece))
        print(" ".join(row_tokens), file=stdout)
