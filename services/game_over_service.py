from typing import Tuple, Callable, Optional
from models.pieces import Piece

class GameOverService:
    def __init__(self, board):
        self.board = board

    def check_game_over(self, target_cell: Tuple[int, int]) -> bool:
        """Checks if the destination cell contains an enemy king, returning True if so."""
        dest_y, dest_x = target_cell
        dest_piece = self.board.get_piece_at(dest_y, dest_x)
        return dest_piece is not None and dest_piece.is_king
