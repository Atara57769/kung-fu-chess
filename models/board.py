from exceptions import UnknownTokenError, RowWidthMismatchError
from models.pieces import get_piece


class Board:
    VALID_PIECES = {'K', 'Q', 'R', 'B', 'N', 'P'}
    VALID_COLORS = {'w', 'b'}
    def __init__(self, board_lines):
        """Initializes the board grid and width."""
        self.grid = []
        self.width = None
        self._parse_and_validate(board_lines)

    def get_piece_at(self, cell_y: int, cell_x: int):
        """Returns the piece at the given cell coordinates."""
        token = self.grid[cell_y][cell_x]
        return get_piece(token)

    def _validate_token(self, token):
        """Validates a single token representing a board cell."""

        if token == '.':
            return
        if len(token) == 2 and token[0] in self.VALID_COLORS and token[1] in self.VALID_PIECES:
            return
        raise UnknownTokenError("ERROR UNKNOWN_TOKEN")

    def _parse_row(self, line):
        """Parses a row line into validated tokens."""
        tokens = line.strip().split()
        for token in tokens:
            self._validate_token(token)
        return tokens

    def _parse_and_validate(self, board_lines):
        """Parses all lines, validates dimensions, and builds the grid."""
        for line in board_lines:
            tokens = self._parse_row(line)
            if self.width is None:
                self.width = len(tokens)
            elif len(tokens) != self.width:
                raise RowWidthMismatchError("ERROR ROW_WIDTH_MISMATCH")
            self.grid.append(tokens)
            
        if self.width is None:
            self.width = 0

    