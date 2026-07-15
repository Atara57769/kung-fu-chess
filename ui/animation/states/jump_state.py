import math
from ui.animation.states.animation_state import AnimationState
from models.game_snapshot import GameSnapshot
from ui.ui_config import JUMP_PEAK_HEIGHT, JUMP_DEFAULT_DURATION

class JumpState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        # 1. Find the active JumpSnapshot for this piece
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

        # If jump is not in snapshot anymore, it finished
        if active_jump is None:
            next_state = self.config.get("physics", {}).get("next_state_when_finished", "short_rest")
            piece_view.change_state(next_state, snapshot)
            return

        # 2. Compute progress
        duration = active_jump.end - active_jump.start
        if duration <= 0:
            duration = JUMP_DEFAULT_DURATION

        current_clock = snapshot.clock
        progress = max(0.0, min(1.0, (current_clock - active_jump.start) / duration))

        # 3. Calculate parabolic height offset
        # Peak height of pixels above the cell from config
        peak_height = JUMP_PEAK_HEIGHT
        # Parabola formula: y = 4 * H * p * (1 - p)
        height_offset = int(4.0 * peak_height * progress * (1.0 - progress))

        # Update position
        top_left = piece_view.geometry.cell_to_top_left_pixel(piece_view.cell)
        piece_view.px = top_left[0]
        piece_view.py = top_left[1] - height_offset

        # 4. Check transition when completed
        if progress >= 1.0:
            next_state = self.config.get("physics", {}).get("next_state_when_finished", "short_rest")
            piece_view.change_state(next_state, snapshot)
