from typing import Tuple
from models.pieces import Piece
from constants import DURATION, COOLDOWN_DURATION
from models.jump import Jump
from models.game_state import GameState

class JumpService:
    def schedule_jump(self, state: GameState, cell: Tuple[int, int], start_time: int, piece: Piece) -> None:
        state.jumps.append(Jump(
            cell=cell,
            start=start_time,
            end=start_time + DURATION,
            piece=piece
        ))
        piece.cooldown_until = start_time + DURATION + COOLDOWN_DURATION