from constants import COLOR_WHITE, COLOR_BLACK, PIECE_PAWN, PIECE_QUEEN
from models.game_state import GameState
from models.pending_move import PendingMove

class PawnPromotion:
    def is_pawn(self, kind: str) -> bool:
        """Checks if the piece kind represents a pawn."""
        return kind == PIECE_PAWN

    def is_promotion_row(self, color: str, to_y: int, board_height: int) -> bool:
        """Checks if the color has reached its respective promotion row."""
        return (color == COLOR_WHITE and to_y == 0) or (color == COLOR_BLACK and to_y == board_height - 1)

    def promote_to_queen(self, piece) -> None:
        """Promotes the piece to a Queen."""
        if piece is not None:
            piece.kind = PIECE_QUEEN

    def apply_pawn_promotion(self, game_state: GameState, move: PendingMove) -> None:
        """Promotes pawns to Queens if they reach the opposite end of the board."""
        board = game_state.board
        to_y = move.to_pos.y
        if move.piece:
            current_piece = move.piece
            
            if current_piece is not None :
                if self.is_pawn(current_piece.kind) and self.is_promotion_row(current_piece.color, to_y, board.height):
                    self.promote_to_queen(current_piece)
