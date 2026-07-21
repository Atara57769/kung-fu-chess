from typing import Tuple
from shared.models.pieces import Piece
from constants import DURATION, COOLDOWN_JUMP
from shared.models.jump import Jump
from shared.models.game_state import GameState

class JumpService:
    def schedule_jump(self, state: GameState, cell: Tuple[int, int], start_time: int, piece: Piece) -> None:
        state.jumps.append(Jump(
            cell=cell,
            start=start_time,
            end=start_time + DURATION,
            piece=piece
        ))
        piece.cooldown_until = start_time + DURATION + COOLDOWN_JUMP