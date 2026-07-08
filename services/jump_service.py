from dataclasses import dataclass
from typing import Tuple, List
from models.pieces import Piece

@dataclass
class Jump:
    cell: Tuple[int, int]
    start: int
    end: int
    piece: Piece

class JumpService:
    def __init__(self):
        self.jumps: List[Jump] = []

    def schedule_jump(self, cell: Tuple[int, int], start_time: int, piece: Piece) -> None:
        duration = piece.get_travel_duration(cell[0], cell[1], cell[0], cell[1]) if piece is not None else Piece.get_travel_duration(None, cell[0], cell[1], cell[0], cell[1])
        self.jumps.append(Jump(
            cell=cell,
            start=start_time,
            end=start_time + duration,
            piece=piece
        ))

    def is_captured_by_airborne_enemy(self, target_cell: Tuple[int, int], arrival_time: int, piece: Piece) -> bool:
        """Checks if the destination contains an active airborne piece of the enemy."""
        for jump in self.jumps:
            if jump.cell == target_cell and jump.start <= arrival_time <= jump.end:
                if jump.piece.color != piece.color:
                    return True
        return False
