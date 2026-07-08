from dataclasses import dataclass
from typing import Tuple, List
from models.pieces import Piece

@dataclass
class PendingMove:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    piece: Piece
    arrival: int

class MoveScheduler:
    def __init__(self, jump_service, move_execution_service):
        self.jump_service = jump_service
        self.move_execution_service = move_execution_service
        self.clock: int = 0
        self.pending_moves: List[PendingMove] = []

    def get_clock(self) -> int:
        return self.clock

    def get_pending_moves(self) -> List[PendingMove]:
        return self.pending_moves

    def schedule_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], piece: Piece, duration: int) -> None:
        arrival = self.clock + duration
        self.pending_moves.append(PendingMove(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=piece,
            arrival=arrival
        ))

    def advance_clock(self, ms: int) -> None:
        self.clock += ms

    def apply_completed_moves(self) -> bool:
        """
        Sorts pending moves and applies all moves whose arrival time has passed.
        Returns True if a game over condition is detected during execution.
        """
        self.pending_moves.sort(key=lambda move: move.arrival)
        
        game_over_detected = False
        remaining_moves = []
        for move in self.pending_moves:
            if move.arrival > self.clock:
                remaining_moves.append(move)
                continue
            
            is_captured = self.jump_service.is_captured_by_airborne_enemy(
                target_cell=move.to_pos,
                arrival_time=move.arrival,
                piece=move.piece
            )
            is_game_over = self.move_execution_service.execute_move(move, is_captured)
            if is_game_over:
                game_over_detected = True
                
        self.pending_moves = remaining_moves
        return game_over_detected
