from typing import Tuple, List, Optional
from models.pieces import Piece
from constants import DURATION
from models.jump import Jump
from models.game_state import GameState

class JumpService:
    def __init__(self, state: Optional[GameState] = None):
        if state is None:
            from services.board_parser import TextBoardParser
            state = GameState(TextBoardParser().parse([]))
        self.state = state

    @property
    def jumps(self) -> List[Jump]:
        return self.state.jumps

    @jumps.setter
    def jumps(self, val: List[Jump]) -> None:
        self.state.jumps = val

    def schedule_jump(self, cell: Tuple[int, int], start_time: int, piece: Piece) -> None:
        self.jumps.append(Jump(
            cell=cell,
            start=start_time,
            end=start_time + DURATION,
            piece=piece
        ))

   