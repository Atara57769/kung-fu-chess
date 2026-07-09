from output.board_parser import BoardParser
from models.cell import Cell
from models.pieces import Piece
from constants import EMPTY_TOKEN

class Board:
    def __init__(self, board_lines):
        """Initializes the board grid, width, and height using BoardParser."""
        self.grid, self.width, self.height = BoardParser.parse(board_lines)

    def get_piece_at(self, cell_y: int, cell_x: int) -> Piece:
        """Returns the piece at the given cell coordinates."""
        val = self.grid[cell_y][cell_x]
        if isinstance(val, Piece):
            return val
        if val is None or val == "." or val == EMPTY_TOKEN:
            return None
        from models.pieces import PieceFactory
        return PieceFactory.get_piece(val, Cell(cell_y, cell_x))

    def is_inside_bounds(self, cell_y: int, cell_x: int) -> bool:
        """Checks whether a cell is inside the board boundaries."""
        return 0 <= cell_y < self.height and 0 <= cell_x < self.width

    def move_piece(self, from_pos: Cell, to_pos: Cell) -> None:
        """Moves a piece from from_pos to to_pos after it has been validated."""
        piece = self.grid[from_pos.y][from_pos.x]
        if piece is not None:
            piece.cell = to_pos
        self.grid[to_pos.y][to_pos.x] = piece
        self.grid[from_pos.y][from_pos.x] = None