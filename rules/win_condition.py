from models.game_state import GameState
from models.cell import Cell
from constants import PIECE_KING

def check_game_over(game_state: GameState, target_cell: Cell) -> bool:
    """Checks if the destination cell contains an enemy king."""
    board = game_state.board
    dest_piece = board.get_piece_at(target_cell)
    if dest_piece is not None and dest_piece.kind == PIECE_KING:
        for move in game_state.pending_moves:
            if move.piece is not None and move.piece.color == dest_piece.color and move.piece.kind == PIECE_KING:
                return False
        return True
    return False
