from abc import ABC, abstractmethod
from typing import List, Optional, Any
from models.board import Board
from models.cell import Cell
from models.pieces import Piece
from exceptions import UnknownTokenError, RowWidthMismatchError

from constants import EMPTY_TOKEN, VALID_COLORS, TOKEN_LENGTH, COLOR_INDEX, KIND_INDEX
from models.piece_type import PieceType

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
            
            if width is None:
                width = len(tokens)
            elif len(tokens) != width:
                raise RowWidthMismatchError("ERROR ROW_WIDTH_MISMATCH")

            row = []
            for x, token in enumerate(tokens):
                if token == EMPTY_TOKEN:
                    row.append(None)
                elif len(token) == TOKEN_LENGTH and token[COLOR_INDEX] in VALID_COLORS and token[KIND_INDEX] in PieceType._value2member_map_:
                    piece = Piece.from_text(token, Cell(y, x))
                    row.append(piece)
                else:
                    raise UnknownTokenError("ERROR UNKNOWN_TOKEN")
            
            grid.append(row)

        if width is None:
            width = 0

        height = len(grid)
        
        return Board(grid, width, height)
