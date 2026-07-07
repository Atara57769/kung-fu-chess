from abc import ABC, abstractmethod

class Piece(ABC):
    def __init__(self, color):
        self.color = color

    @abstractmethod
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        """Determines if the move from (from_y, from_x) to (to_y, to_x) is legal for this piece."""
        pass

    def _is_path_clear(self, board, from_y, from_x, to_y, to_x) -> bool:
        """Helper to verify if the path between two cells is clear of other pieces (excluding the endpoints)."""
        dy = to_y - from_y
        dx = to_x - from_x
        abs_dy = abs(dy)
        abs_dx = abs(dx)

        if dy == 0:
            step = 1 if dx > 0 else -1
            for x in range(from_x + step, to_x, step):
                if board.grid[from_y][x] != '.':
                    return False
        elif dx == 0:
            step = 1 if dy > 0 else -1
            for y in range(from_y + step, to_y, step):
                if board.grid[y][from_x] != '.':
                    return False
        elif abs_dx == abs_dy:
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            for i in range(1, abs_dx):
                if board.grid[from_y + i * step_y][from_x + i * step_x] != '.':
                    return False
        return True


class King(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        dy = to_y - from_y
        dx = to_x - from_x
        return abs(dx) <= 1 and abs(dy) <= 1 and not (dx == 0 and dy == 0)


class Rook(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        dy = to_y - from_y
        dx = to_x - from_x
        if not (dx == 0 or dy == 0) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_y, from_x, to_y, to_x)


class Bishop(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        dy = to_y - from_y
        dx = to_x - from_x
        if abs(dx) != abs(dy) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_y, from_x, to_y, to_x)


class Queen(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        dy = to_y - from_y
        dx = to_x - from_x
        if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_y, from_x, to_y, to_x)


class Knight(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        dy = to_y - from_y
        dx = to_x - from_x
        abs_dy = abs(dy)
        abs_dx = abs(dx)
        return (abs_dx == 1 and abs_dy == 2) or (abs_dx == 2 and abs_dy == 1)


class Pawn(Piece):
    def is_legal_move(self, board, from_y, from_x, to_y, to_x) -> bool:
        return True


PIECE_CLASSES = {
    'K': King,
    'Q': Queen,
    'R': Rook,
    'B': Bishop,
    'N': Knight,
    'P': Pawn
}


def get_piece(token) -> Piece:
    if token == '.':
        return None
    if len(token) < 2:
        return None
    color = token[0]
    piece_type = token[1]
    cls = PIECE_CLASSES.get(piece_type)
    if cls:
        return cls(color)
    return None
