from typing import Optional
from models.board import Board
from models.cell import Cell
from models.pending_move import PendingMove

class BoardRules:
    def is_move_valid(self, board: Board, cell_from: Cell, cell_to: Cell, pending_moves: Optional[list[PendingMove]] = None) -> bool:
        """
        Orchestrates checking all the move validation rules.
        """
        
        if self.friendly_destination(board, cell_from, cell_to):
            return False
        if self.is_destination_reserved(cell_to, pending_moves):
            return False

        return True

    def friendly_destination(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Checks if the destination cell contains a friendly piece.
        Returns True if the destination contains a friendly piece.
        """
        if cell_from is None or cell_to is None:
            return False
        if not board.is_inside_bounds(cell_from.y, cell_from.x) or not board.is_inside_bounds(cell_to.y, cell_to.x):
            return False
        
        piece = board.get_piece_at(cell_from)
        if piece is None:
            return False
        
        dest_piece = board.get_piece_at(cell_to)
        if dest_piece is None:
            return False
        
        return dest_piece.color == piece.color

    def is_destination_reserved(self, cell: Cell, pending_moves: Optional[list[PendingMove]]) -> bool:
        """
        Checks if a cell is the target destination of any pending move.
        Returns True if the destination cell is reserved.
        """
        if cell is None or pending_moves is None:
            return False
        return any(move.to_pos == cell for move in pending_moves)
