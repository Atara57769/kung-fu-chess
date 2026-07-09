from typing import List, Optional, Tuple
from models.cell import Cell
from models.pieces import Piece, PieceFactory
from exceptions import UnknownTokenError, RowWidthMismatchError
from constants import EMPTY_TOKEN, VALID_COLORS, VALID_PIECES

class BoardParser:
    @staticmethod
    def parse(board_lines: List[str]) -> Tuple[List[List[Optional[Piece]]], int, int]:
        """
        Parses all lines, validates dimensions, and builds a grid of Piece objects or None.
        Returns a tuple of (grid, width, height).
        """
        grid = []
        width = None

        for y, line in enumerate(board_lines):
            tokens = line.strip().split()
            
            # Validate row width consistency
            if width is None:
                width = len(tokens)
            elif len(tokens) != width:
                raise RowWidthMismatchError("ERROR ROW_WIDTH_MISMATCH")

            row = []
            for x, token in enumerate(tokens):
                # Validate token format
                if token == EMPTY_TOKEN:
                    row.append(None)
                elif len(token) == 2 and token[0] in VALID_COLORS and token[1] in VALID_PIECES:
                    # Create Piece object
                    piece = PieceFactory.get_piece(token, Cell(y, x))
                    row.append(piece)
                else:
                    raise UnknownTokenError("ERROR UNKNOWN_TOKEN")
            
            grid.append(row)

        if width is None:
            width = 0

        height = len(grid)
        return grid, width, height
