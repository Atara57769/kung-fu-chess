from ui.animation.states.animation_state import AnimationState
from ui.animation.state_types import AnimationStateId
from models.game_snapshot import GameSnapshot

class ShortRestState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        top_left = piece_view.geometry.cell_to_top_left_pixel(piece_view.cell)
        piece_view.px, piece_view.py = top_left

        piece_snap = None
        board = snapshot.board
        if 0 <= piece_view.cell.y < board.height and 0 <= piece_view.cell.x < board.width:
            p = board.grid[piece_view.cell.y][piece_view.cell.x]
            if p is not None and p.color == piece_view.color and p.kind == piece_view.kind:
                piece_snap = p
                
        if piece_snap is None:
            return

        if snapshot.clock >= piece_snap.cooldown_until:
            next_state = self.config.get("physics", {}).get("next_state_when_finished", AnimationStateId.IDLE)
            piece_view.change_state(next_state, snapshot)

