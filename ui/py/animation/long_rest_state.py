from ui.py.animation.animation_state import AnimationState
from models.game_snapshot import GameSnapshot

class LongRestState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        # 1. Update visual position to match logical cell
        top_left = piece_view.geometry.cell_to_top_left_pixel(piece_view.cell)
        piece_view.px, piece_view.py = top_left

        # 2. Find matching PieceSnapshot in board grid to check cooldown status
        piece_snap = None
        board = snapshot.board
        if 0 <= piece_view.cell.y < board.height and 0 <= piece_view.cell.x < board.width:
            p = board.grid[piece_view.cell.y][piece_view.cell.x]
            if p is not None and p.color == piece_view.color and p.kind == piece_view.kind:
                piece_snap = p
        
        if piece_snap is None:
            return

        if snapshot.clock >= piece_snap.cooldown_until:
            piece_view.change_state("idle", snapshot)
