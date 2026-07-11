from abc import ABC, abstractmethod
from typing import List, Optional, Any
from models.board import Board
from models.cell import Cell
from models.pieces import Piece
from factory import PieceFactory
from exceptions import UnknownTokenError, RowWidthMismatchError
from constants import EMPTY_TOKEN, VALID_COLORS, VALID_PIECES

class BoardParser(ABC):
    @abstractmethod
    def parse(self, data: Any) -> Board:
        """Parses the data and returns a Board object."""
        pass

class TextBoardParser(BoardParser):
    def parse(self, board_lines: List[str]) -> Board:
        """
        Parses all lines, validates dimensions, and builds a Board object.
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
                    piece = PieceFactory.from_text(token, Cell(y, x))
                    row.append(piece)
                else:
                    raise UnknownTokenError("ERROR UNKNOWN_TOKEN")
            
            grid.append(row)

        if width is None:
            width = 0

        height = len(grid)
        
        # Instantiate Board and return it
        return Board(grid, width, height)
