from exceptions import UnknownTokenError, RowWidthMismatchError


class Board:
    def __init__(self, board_lines):
        """Initializes the board grid and width."""
        self.grid = []
        self.width = None
        self._parse_and_validate(board_lines)

    def _validate_token(self, token):
        """Validates a single token representing a board cell."""
        valid_pieces = {'K', 'Q', 'R', 'B', 'N', 'P'}
        valid_colors = {'w', 'b'}
        if token == '.':
            return
        if len(token) == 2 and token[0] in valid_colors and token[1] in valid_pieces:
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

    def print(self):
        """Prints the board in canonical space-separated format."""
        for row in self.grid:
            print(" ".join(row))
