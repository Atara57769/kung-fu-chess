import math
from ui.animation.states.animation_state import AnimationState
from ui.animation.state_types import AnimationStateId
from models.game_snapshot import GameSnapshot
from ui.ui_config import JUMP_PEAK_HEIGHT, JUMP_DEFAULT_DURATION

class JumpState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        active_jump = None
        for j in snapshot.jumps:
            if snapshot.clock >= j.end:
                continue
            jump_cell_y, jump_cell_x = j.cell
            if (jump_cell_y == piece_view.cell.y and 
                    jump_cell_x == piece_view.cell.x and 
                    j.piece.color == piece_view.color and 
                    j.piece.kind == piece_view.kind):
                active_jump = j
                break

        if active_jump is None:
            next_state = self.config.get("physics", {}).get("next_state_when_finished", AnimationStateId.SHORT_REST)
            piece_view.change_state(next_state, snapshot)
            return

        duration = active_jump.end - active_jump.start
        if duration <= 0:
            duration = JUMP_DEFAULT_DURATION

        current_clock = snapshot.clock
        progress = max(0.0, min(1.0, (current_clock - active_jump.start) / duration))

        peak_height = JUMP_PEAK_HEIGHT
        height_offset = int(4.0 * peak_height * progress * (1.0 - progress))

        top_left = piece_view.geometry.cell_to_top_left_pixel(piece_view.cell)
        piece_view.px = top_left[0]
        piece_view.py = top_left[1] - height_offset

        if progress >= 1.0:  # pragma: no cover
            next_state = self.config.get("physics", {}).get("next_state_when_finished", AnimationStateId.SHORT_REST)
            piece_view.change_state(next_state, snapshot)

