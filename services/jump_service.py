from typing import Tuple, List
from models.pieces import Piece
from constants import DURATION
from models.jump import Jump

class JumpService:
    def __init__(self):
        self.jumps: List[Jump] = []

    def schedule_jump(self, cell: Tuple[int, int], start_time: int, piece: Piece) -> None:
        self.jumps.append(Jump(
            cell=cell,
            start=start_time,
            end=start_time + DURATION,
            piece=piece
        ))

    def is_captured_by_airborne_enemy(self, target_cell: Tuple[int, int], arrival_time: int, piece: Piece) -> bool:
        """Checks if the destination contains an active airborne piece of the enemy."""
        for jump in self.jumps:
            if jump.cell == target_cell and jump.start <= arrival_time <= jump.end:
                if jump.piece.color != piece.color:
                    return True
        return False
