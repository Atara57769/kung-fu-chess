from typing import List, Tuple, Optional, Callable
from models.pieces import Piece
from models.cell import Cell
from models.game_state import GameState
from services.move_scheduler import MoveScheduler

class MoveValidationService:
    def __init__(self, state: GameState, move_scheduler: MoveScheduler):
        self.state = state
        self.board = state.board
        self.move_scheduler = move_scheduler

    def is_within_bounds(self, row: int, col: int) -> bool:
        """Checks if the cell Cells (row, col) are within the board boundaries."""
        return 0 <= col < self.board.width and 0 <= row < self.board.height

    def is_piece_moving(self, row: int, col: int) -> bool:
        """Checks if a piece at (row, col) is currently in transit as a source of a pending move."""
        return any(move.from_pos == Cell(row, col) for move in self.move_scheduler.get_pending_moves())

    def is_destination_reserved(self, row: int, col: int) -> bool:
        """Checks if a cell (row, col) is the target destination of any pending move."""
        return any(move.to_pos == Cell(row, col) for move in self.move_scheduler.get_pending_moves())

    def is_legal_move(self, piece: Piece, from_pos: Cell, to_pos: Cell) -> bool:
        if piece is None:
            return True
        from rules.piece_rules import RULES
        rule = RULES.get(piece.kind)
        if rule:
            return rule.is_move_valid(self.board, from_pos, to_pos)
        return False

    def validate_move(self, sel_y: int, sel_x: int, to_y: int, to_x: int) -> bool:
        """
        Validates if the move from (sel_y, sel_x) to (to_y, to_x) is valid.
        Returns True if valid, False otherwise.
        """
        if not self.is_within_bounds(to_y, to_x):
            return False

        sel_piece = self.board.get_piece_at(sel_y, sel_x)
        piece = self.board.get_piece_at(to_y, to_x)

        # If clicking another friendly piece, it's not a move (selection will be updated outside)
        if piece is not None and sel_piece is not None and piece.color == sel_piece.color:
            return False

        # Check transit validation
        if self.is_piece_moving(sel_y, sel_x) or self.is_destination_reserved(to_y, to_x):
            return False

        # Check legality
        return self.is_legal_move(sel_piece, Cell(sel_y, sel_x), Cell(to_y, to_x))

    def validate_jump(self, cell_y: int, cell_x: int) -> bool:
        """Validates if a jump can be performed on the given cell Cells."""
        if not self.is_within_bounds(cell_y, cell_x):
            return False
        piece = self.board.get_piece_at(cell_y, cell_x)
        if piece is None:
            return False
        if self.is_piece_moving(cell_y, cell_x) or self.is_destination_reserved(cell_y, cell_x):
            return False
        return True
