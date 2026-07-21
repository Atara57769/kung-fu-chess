from client.ui.animation.states.animation_state import AnimationState
from shared.models.game_snapshot import GameSnapshot

class IdleState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        top_left = piece_view.geometry.cell_to_top_left_pixel(piece_view.cell)
        piece_view.px, piece_view.py = top_left

        for move in snapshot.pending_moves:
            if (move.from_pos == piece_view.cell and 
                    move.piece.color == piece_view.color and 
                    move.piece.kind == piece_view.kind):
                piece_view.change_state("move", snapshot)
                return

        for jump in snapshot.jumps:
            if snapshot.clock >= jump.end:
                continue
            jump_cell_y, jump_cell_x = jump.cell
            if (jump_cell_y == piece_view.cell.y and 
                    jump_cell_x == piece_view.cell.x and 
                    jump.piece.color == piece_view.color and 
                    jump.piece.kind == piece_view.kind):
                piece_view.change_state("jump", snapshot)
                return
