from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece, PieceStatus
from models.pending_move import PendingMove

class MoveScheduler:
    def create_pending_move(
        self,
        from_cell: Cell,
        to_cell: Cell,
        piece: Optional[Piece],
        arrival: int,
        is_captured: bool = False
    ) -> PendingMove:
        """Creates a PendingMove instance."""
        return PendingMove(
            from_pos=from_cell,
            to_pos=to_cell,
            piece=piece,
            arrival=arrival,
            is_captured=is_captured,
        )

    def add_to_pending(self, state: GameState, pending_move: PendingMove) -> None:
        """Appends the PendingMove instance to state.pending_moves."""
        state.pending_moves.append(pending_move)
        if pending_move.piece is not None:
            pending_move.piece.status = PieceStatus.MOVING


