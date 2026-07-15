from typing import Optional
from models.board import Board
from models.pieces import Piece, PieceStatus
from models.cell import Cell
from models.pending_move import PendingMove
from constants import COLOR_WHITE, COLOR_BLACK
from rules.board_rules import BoardRules

class RuleEngine:
    def __init__(self, board_rules: BoardRules = None):
        self.board_rules = board_rules or BoardRules()

    def is_move_valid(self, board: Board, cell_from: Cell, cell_to: Cell, pending_moves: Optional[list[PendingMove]] = None) -> bool:
        """
        Validates a move on the board from cell_from to cell_to.
        Calls the check functions and returns True if all are True.
        """
        if self.outside_board(board, cell_from, cell_to):
            return False
        if self.empty_source(board, cell_from):
            return False
        if self.is_piece_moving(cell_from, board):
            return False
        if not self.board_rules.is_move_valid(board, cell_from, cell_to, pending_moves):
            return False
        if not self.is_piece_move_valid(board, cell_from, cell_to):
            return False

        return True

    def is_piece_moving(self, cell: Cell, board: Optional[Board]) -> bool:
        """
        Checks if a piece at the cell is currently in transit as a source of a pending move.
        Returns True if the piece is moving.
        """
        if cell is None or board is None:
            return False
        piece = board.get_piece_at(cell)
        if piece is None:
            return False
        return piece.status == PieceStatus.MOVING



    def outside_board(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Checks if either cell is outside the board boundaries.
        Returns True if at least one cell is outside the board boundaries.
        """
        if cell_from is None or cell_to is None:
            return True
        return not board.is_inside_bounds(cell_from.y, cell_from.x) or not board.is_inside_bounds(cell_to.y, cell_to.x)

    def empty_source(self, board: Board, cell_from: Cell) -> bool:
        """
        Checks if the source cell contains a piece.
        Returns True if the source cell is empty, and False otherwise.
        """
        if cell_from is None or not board.is_inside_bounds(cell_from.y, cell_from.x):
            return True
        piece = board.get_piece_at(cell_from)
        return piece is None

    def is_piece_move_valid(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Checks if the move is legal according to piece-specific rules.
        Returns True if the move is legal.
        """
        if cell_from is None or cell_to is None:
            return False
        if not board.is_inside_bounds(cell_from.y, cell_from.x):
            return False
        
        piece = board.get_piece_at(cell_from)
        if piece is None:
            return False
        
        from rules.piece_rules import RULES
        rule = RULES.get(piece.kind)
        if rule:
            return rule.is_move_valid(board, cell_from, cell_to)
        return False
