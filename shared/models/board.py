from typing import List, Optional
from shared.models.cell import Cell
from shared.models.pieces import Piece
from shared.constants import EMPTY_TOKEN

class Board:
    def __init__(self, grid: List[List[Optional[Piece]]], width: int, height: int):
        self.grid = grid
        self.width = width
        self.height = height

    def get_piece_at(self, cell: Cell) -> Optional[Piece]:
        """Returns the piece at the given cell."""
        return self.grid[cell.y][cell.x]

    def is_inside_bounds(self, cell_y: int, cell_x: int) -> bool:
        """Checks whether a cell is inside the board boundaries."""
        return 0 <= cell_y < self.height and 0 <= cell_x < self.width

    def move_piece(self, from_pos: Cell, to_pos: Cell, piece: Piece) -> None:
        """Moves a piece from from_pos to to_pos after it has been validated."""
        source_y, source_x = from_pos.y, from_pos.x
        if piece.cell is not None:
            source_y, source_x = piece.cell.y, piece.cell.x

        grid_piece = self.grid[source_y][source_x]
        match = (grid_piece is piece)

        piece.cell = to_pos
        self.grid[to_pos.y][to_pos.x] = piece
        if match:
            if (source_y, source_x) != (to_pos.y, to_pos.x):
                self.grid[source_y][source_x] = None
