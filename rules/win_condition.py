from typing import Optional
from models.color import Color
from models.game_state import GameState
from models.cell import Cell
from models.piece_type import PieceType

def check_game_over(game_state: GameState, target_cell: Cell) -> Optional[Color]:
    """Checks if the destination cell contains an enemy king. Returns the winning Color or None."""
    board = game_state.board
    dest_piece = board.get_piece_at(target_cell)
    if dest_piece is not None and dest_piece.kind == PieceType.KING:
        for move in game_state.pending_moves:
            if move.piece is not None and move.piece.color == dest_piece.color and move.piece.kind == PieceType.KING:
                return None
        return Color.WHITE if dest_piece.color == Color.BLACK else Color.BLACK
    return None

