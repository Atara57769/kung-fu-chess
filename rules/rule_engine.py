from models.board import Board
from models.pieces import Piece
from models.cell import Cell

class RuleEngine:
    def is_move_valid(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Validates a move on the board from cell_from to cell_to.
        Calls the four check functions and returns True if all are True.
        """
        if self.outside_board(board, cell_from, cell_to):
            return False
        if self.empty_source(board, cell_from):
            return False
        if self.friendly_destination(board, cell_from, cell_to):
            return False
        if not self.illegal_to_move(board, cell_from, cell_to):
            return False

        return True

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
        piece = board.get_piece_at(cell_from.y, cell_from.x)
        return piece is None

    def friendly_destination(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Checks if the destination cell contains a friendly piece.
        Returns True if the destination contains a friendly piece.
        """
        if cell_from is None or cell_to is None:
            return False
        if not board.is_inside_bounds(cell_from.y, cell_from.x) or not board.is_inside_bounds(cell_to.y, cell_to.x):
            return False
        
        piece = board.get_piece_at(cell_from.y, cell_from.x)
        if piece is None:
            return False
        
        dest_piece = board.get_piece_at(cell_to.y, cell_to.x)
        if dest_piece is None:
            return False
        
        return dest_piece.color == piece.color

    def illegal_to_move(self, board: Board, cell_from: Cell, cell_to: Cell) -> bool:
        """
        Checks if the move is legal according to piece-specific rules.
        Returns True if the move is legal.
        """
        if cell_from is None or cell_to is None:
            return False
        if not board.is_inside_bounds(cell_from.y, cell_from.x):
            return False
        
        piece = board.get_piece_at(cell_from.y, cell_from.x)
        if piece is None:
            return False
        
        from rules.piece_rules import RULES
        rule = RULES.get(piece.kind)
        if rule:
            return rule.is_move_valid(board, cell_from, cell_to)
        return False