from typing import List, Optional
from models.cell import Cell
from models.pieces import Piece
from constants import EMPTY_TOKEN, PIECE_QUEEN, PIECE_PAWN

class Board:
    def __init__(self, grid: List[List[Optional[Piece]]], width: int, height: int):
        self.grid = grid
        self.width = width
        self.height = height

    def get_piece_at(self, cell_y: int, cell_x: int) -> Piece:
        """Returns the piece at the given cell coordinates."""
        return self.grid[cell_y][cell_x]

    def is_inside_bounds(self, cell_y: int, cell_x: int) -> bool:
        """Checks whether a cell is inside the board boundaries."""
        return 0 <= cell_y < self.height and 0 <= cell_x < self.width

    def move_piece(self, from_pos: Cell, to_pos: Cell, piece: Piece) -> None:
        """Moves a piece from from_pos to to_pos after it has been validated."""
        source_y, source_x = from_pos.y, from_pos.x
        if piece.cell is not None:
            source_y, source_x = piece.cell.y, piece.cell.x

        grid_piece = self.grid[source_y][source_x]
        match = (grid_piece is not None and 
                 grid_piece.color == piece.color and 
                 (grid_piece.kind == piece.kind or (grid_piece.kind == PIECE_QUEEN and piece.kind == PIECE_PAWN)))

        if not match:
            piece.cell = to_pos
            self.grid[to_pos.y][to_pos.x] = piece
        else:
            piece.cell = to_pos
            self.grid[to_pos.y][to_pos.x] = piece
            if (source_y, source_x) != (to_pos.y, to_pos.x):
                self.grid[source_y][source_x] = None
