from abc import ABC, abstractmethod
from constants import EMPTY_TOKEN
from models.cell import Cell

class BaseRule(ABC):
    @abstractmethod
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        pass


class SlidingRule(BaseRule):
    def _is_path_clear(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        """Helper to verify if the path between two cells is clear of other pieces (excluding the endpoints)."""
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        abs_dy = abs(dy)
        abs_dx = abs(dx)

        if dy == 0:
            step = 1 if dx > 0 else -1
            for x in range(from_pos.x + step, to_pos.x, step):
                if board.get_piece_at(from_pos.y, x) is not None:
                    return False
        elif dx == 0:
            step = 1 if dy > 0 else -1
            for y in range(from_pos.y + step, to_pos.y, step):
                if board.get_piece_at(y, from_pos.x) is not None:
                    return False
        elif abs_dx == abs_dy:
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            for i in range(1, abs_dx):
                if board.get_piece_at(from_pos.y + i * step_y, from_pos.x + i * step_x) is not None:
                    return False
        return True


class RookRule(SlidingRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if not (dx == 0 or dy == 0) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class BishopRule(SlidingRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if abs(dx) != abs(dy) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class QueenRule(SlidingRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)) or (dx == 0 and dy == 0):
            return False
        return self._is_path_clear(board, from_pos, to_pos)


class KnightRule(BaseRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        abs_dy = abs(dy)
        abs_dx = abs(dx)
        return (abs_dx == 1 and abs_dy == 2) or (abs_dx == 2 and abs_dy == 1)


class KingRule(BaseRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x
        return abs(dx) <= 1 and abs(dy) <= 1 and not (dx == 0 and dy == 0)


class PawnRule(BaseRule):
    def is_move_valid(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        piece = board.get_piece_at(from_pos.y, from_pos.x)
        if piece is None:
            return False

        target_piece = board.get_piece_at(to_pos.y, to_pos.x)
        H = board.height
        if piece.color == 'w':
            expected_dy = -1
            start_row = H - 2 if H >= 5 else H - 1
        else:
            expected_dy = 1
            start_row = 1 if H >= 5 else 0

        dy = to_pos.y - from_pos.y
        dx = to_pos.x - from_pos.x

        if dy == expected_dy:
            if dx == 0:
                return target_piece is None
            elif abs(dx) == 1:
                return target_piece is not None
        elif dy == 2 * expected_dy and from_pos.y == start_row and dx == 0:
            intermediate_piece = board.get_piece_at(from_pos.y + expected_dy, from_pos.x)
            return target_piece is None and intermediate_piece is None

        return False


RULES = {
    "R": RookRule(),
    "B": BishopRule(),
    "Q": QueenRule(),
    "N": KnightRule(),
    "K": KingRule(),
    "P": PawnRule(),
}
