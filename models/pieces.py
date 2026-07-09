from abc import ABC, abstractmethod
from constants import EMPTY_TOKEN
from models.cell import Cell

class Piece(ABC):
    def __init__(self, color):
        self.color = color

    @property
    def is_king(self) -> bool:
        """Returns True if the piece is a King."""
        return False

    @property
    def is_pawn(self) -> bool:
        """Returns True if the piece is a Pawn."""
        return False

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the single-character name representing the piece type."""
        pass

    @property
    def token(self) -> str:
        """Returns the two-character string representing the piece (e.g. 'wK')."""
        return self.color + self.name

    @abstractmethod
    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        """Determines if the move from from_pos to to_pos is legal for this piece."""
        pass

    def promote(self, to_y: int, grid_height: int) -> str:
        """Returns the promoted token (or current token by default)."""
        return self.token

    def _is_path_clear(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        """Helper to verify if the path between two cells is clear of other pieces (excluding the endpoints)."""
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        abs_dy = abs(dy)
        abs_dx = abs(dx)

        if dy == 0:
            step = 1 if dx > 0 else -1
            for x in range(from_pos.x + step, to_pos.x, step):
                if board.grid[from_pos.y][x] != EMPTY_TOKEN:
                    return False
        elif dx == 0:
            step = 1 if dy > 0 else -1
            for y in range(from_pos.y + step, to_pos.y, step):
                if board.grid[y][from_pos.x] != EMPTY_TOKEN:
                    return False
        elif abs_dx == abs_dy:
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            for i in range(1, abs_dx):
                if board.grid[from_pos.y + i * step_y][from_pos.x + i * step_x] != EMPTY_TOKEN:
                    return False
        return True


class King(Piece):
    @property
    def is_king(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return 'K'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        return abs(dx) <= 1 and abs(dy) <= 1 and not (dx == 0 and dy == 0)


class Rook(Piece):
    @property
    def name(self) -> str:
        return 'R'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if not (dx == 0 or dy == 0) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class Bishop(Piece):
    @property
    def name(self) -> str:
        return 'B'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if abs(dx) != abs(dy) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class Queen(Piece):
    @property
    def name(self) -> str:
        return 'Q'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class Knight(Piece):
    @property
    def name(self) -> str:
        return 'N'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        abs_dy = abs(dy)
        abs_dx = abs(dx)
        return (abs_dx == 1 and abs_dy == 2) or (abs_dx == 2 and abs_dy == 1)




class Pawn(Piece):
    @property
    def is_pawn(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return 'P'

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        target_token = board.grid[to_pos.y][to_pos.x]
        H = board.height
        if self.color == 'w':
            expected_dy = -1
            start_row = H - 2 if H >= 5 else H - 1
        else:
            expected_dy = 1
            start_row = 1 if H >= 5 else 0

        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x

        if dy == expected_dy:
            if dx == 0:
                return target_token == EMPTY_TOKEN
            elif abs(dx) == 1:
                return target_token != EMPTY_TOKEN
        elif dy == 2 * expected_dy and from_pos.y == start_row and dx == 0:
            intermediate_token = board.grid[from_pos.y + expected_dy][from_pos.x]
            return target_token == EMPTY_TOKEN and intermediate_token == EMPTY_TOKEN

        return False

    def promote(self, to_y: int, grid_height: int) -> str:
        """Promotes a pawn to a queen if it reaches the opposite back rank."""
        is_white_promotion = (self.color == 'w' and to_y == 0)
        is_black_promotion = (self.color == 'b' and to_y == grid_height - 1)
        if is_white_promotion or is_black_promotion:
            from models.pieces import Queen
            return Queen(self.color).token
        return self.token


PIECE_CLASSES = {
    'K': King,
    'Q': Queen,
    'R': Rook,
    'B': Bishop,
    'N': Knight,
    'P': Pawn
}


def get_piece(token) -> Piece:
    if token == EMPTY_TOKEN:
        return None
    if len(token) < 2:
        return None
    color = token[0]
    piece_type = token[1]
    cls = PIECE_CLASSES.get(piece_type)
    if cls:
        return cls(color)
    return None
