from client.ui.animation.states.animation_state import AnimationState
from client.ui.animation.state_types import AnimationStateId
from shared.models.game_snapshot import GameSnapshot
from client.ui.ui_config import MOVE_DEFAULT_DURATION

class MoveState(AnimationState):
    def on_enter(self, piece_view, snapshot: GameSnapshot) -> None:
        super().on_enter(piece_view, snapshot)
        move = self._find_active_move(piece_view, snapshot)
        if move is not None:
            piece_view.target_cell = move.to_pos
            self.arrival = move.arrival
        self.start_clock = snapshot.clock

    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        active_move = self._find_active_move(piece_view, snapshot)
        if active_move is None:
            self._transition_to_next_state(piece_view, snapshot)
            return

        progress = self._calculate_progress(snapshot.clock)
        self._interpolate_position(piece_view, active_move, progress)

        if progress >= 1.0:
            self._handle_finished(piece_view, active_move, snapshot)

    def _find_active_move(self, piece_view, snapshot: GameSnapshot):
        for move in snapshot.pending_moves:
            if (move.from_pos == piece_view.cell and 
                    move.piece.color == piece_view.color and 
                    move.piece.kind == piece_view.kind):
                return move
        return None

    def _calculate_progress(self, current_clock: int) -> float:
        duration = self.arrival - self.start_clock
        if duration <= 0:
            duration = MOVE_DEFAULT_DURATION

        if current_clock >= self.arrival:
            return 1.0
        return max(0.0, (current_clock - self.start_clock) / duration)

    def _interpolate_position(self, piece_view, active_move, progress: float) -> None:
        path = active_move.path
        n_cells = len(path)
        if n_cells <= 1:
            top_left = piece_view.geometry.cell_to_top_left_pixel(active_move.to_pos)
            piece_view.px, piece_view.py = top_left
        else:
            scaled_progress = progress * (n_cells - 1)
            idx = int(scaled_progress)
            if idx >= n_cells - 1:
                idx = n_cells - 2
                seg_prog = 1.0
            else:
                seg_prog = scaled_progress - idx

            cell_a = path[idx]
            cell_b = path[idx + 1]

            xa, ya = piece_view.geometry.cell_to_top_left_pixel(cell_a)
            xb, yb = piece_view.geometry.cell_to_top_left_pixel(cell_b)

            piece_view.px = int(xa + (xb - xa) * seg_prog)
            piece_view.py = int(ya + (yb - ya) * seg_prog)

    def _transition_to_next_state(self, piece_view, snapshot: GameSnapshot) -> None:
        next_state = self.config.get("physics", {}).get("next_state_when_finished", AnimationStateId.LONG_REST)
        piece_view.change_state(next_state, snapshot)

    def _handle_finished(self, piece_view, active_move, snapshot: GameSnapshot) -> None:
        piece_view.cell = active_move.to_pos
        self._transition_to_next_state(piece_view, snapshot)
