from typing import Optional
from models.cell import Cell
from models.pieces import Piece
from models.pending_move import PendingMove
from models.game_state import GameState
from constants import DURATION
from models.piece_type import PieceType

class CollisionService:
    def get_move_duration(self, from_cell: Cell, to_cell: Cell, piece: Optional[Piece]) -> int:
        dy = to_cell.y - from_cell.y
        dx = to_cell.x - from_cell.x
        if piece is not None and piece.kind == PieceType.KNIGHT:
            distance = abs(dy) + abs(dx)
        else:
            distance = max(abs(dy), abs(dx))
        return distance * DURATION

    def moves_meet_in_middle(self, m1: PendingMove, m2: PendingMove) -> bool:
        dur1 = self.get_move_duration(m1.from_pos, m1.to_pos, m1.piece)
        dur2 = self.get_move_duration(m2.from_pos, m2.to_pos, m2.piece)
        if dur1 == 0 or dur2 == 0:
            return False

        t1_start = m1.arrival - dur1
        t1_end = m1.arrival
        t2_start = m2.arrival - dur2
        t2_end = m2.arrival

        t_min = max(t1_start, t2_start)
        t_max = min(t1_end, t2_end)
        if t_min > t_max:
            return False

        dx1 = m1.to_pos.x - m1.from_pos.x
        dy1 = m1.to_pos.y - m1.from_pos.y
        dx2 = m2.to_pos.x - m2.from_pos.x
        dy2 = m2.to_pos.y - m2.from_pos.y

        A_x = dx1 / dur1 - dx2 / dur2
        B_x = m2.from_pos.x - m1.from_pos.x - dx2 * t2_start / dur2 + dx1 * t1_start / dur1

        A_y = dy1 / dur1 - dy2 / dur2
        B_y = m2.from_pos.y - m1.from_pos.y - dy2 * t2_start / dur2 + dy1 * t1_start / dur1

        t_sol = None
        if abs(A_x) > 1e-9:
            t_candidate = B_x / A_x
            if abs(A_y) > 1e-9:
                if abs(A_y * t_candidate - B_y) < 1e-9:
                    t_sol = t_candidate
            else:
                if abs(B_y) < 1e-9:
                    t_sol = t_candidate
        else:
            if abs(B_x) < 1e-9:
                if abs(A_y) > 1e-9:
                    t_sol = B_y / A_y
                else:
                    if abs(B_y) < 1e-9:
                        t_sol = t_min

        if t_sol is not None:
            if t_min - 1e-9 <= t_sol <= t_max + 1e-9:
                return True

        return False

    def check_mid_move_collision(self, state: GameState, new_move: PendingMove) -> bool:
        if new_move.piece is None or new_move.piece.kind == PieceType.KNIGHT:
            return False

        for existing in state.pending_moves:
            if existing.piece is None or existing.piece.kind == PieceType.KNIGHT:
                continue
            if existing.is_captured:
                continue

            if self.moves_meet_in_middle(existing, new_move):
                return True

        return False
