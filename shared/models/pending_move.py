from dataclasses import dataclass, field
from typing import List
from shared.models.cell import Cell
from shared.models.pieces import Piece
from shared.models.piece_type import PieceType

@dataclass
class PendingMove:
    from_pos: Cell
    to_pos: Cell
    piece: Piece
    arrival: int
    is_captured: bool = False
    path: List[Cell] = field(init=False)

    def __post_init__(self):
        self.path = self._calculate_path()

    def _calculate_path(self) -> List[Cell]:
        if self.from_pos == self.to_pos:
            return [self.from_pos]
        if self._is_knight_move():
            return [self.from_pos, self.to_pos]
        if self._is_straight_move():
            return self._generate_straight_path()
        return [self.from_pos, self.to_pos]

    def _is_knight_move(self) -> bool:
        try:
            return self.piece.kind == PieceType.KNIGHT
        except AttributeError:
            return False

    def _is_straight_move(self) -> bool:
        dy = self.to_pos.y - self.from_pos.y
        dx = self.to_pos.x - self.from_pos.x
        return (dy == 0) or (dx == 0) or (abs(dx) == abs(dy))

    def _generate_straight_path(self) -> List[Cell]:
        dy = self.to_pos.y - self.from_pos.y
        dx = self.to_pos.x - self.from_pos.x
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        steps = max(abs(dx), abs(dy))
        return [
            Cell(self.from_pos.y + i * step_y, self.from_pos.x + i * step_x)
            for i in range(steps + 1)
        ]


