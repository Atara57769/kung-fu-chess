from ui.py.animation.animation_state import AnimationState
from models.game_snapshot import GameSnapshot

class MoveState(AnimationState):
    def on_enter(self, piece_view, snapshot: GameSnapshot) -> None:
        super().on_enter(piece_view, snapshot)
        for move in snapshot.pending_moves:
            if (move.from_pos == piece_view.cell and 
                    move.piece.color == piece_view.color and 
                    move.piece.kind == piece_view.kind):
                piece_view.target_cell = move.to_pos
                self.arrival = move.arrival
                break
        self.start_clock = snapshot.clock

    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        self.advance_frames(dt)

        # 1. Find the corresponding PendingMoveSnapshot
        active_move = None
        for move in snapshot.pending_moves:
            # We match the move that has either start or end at our cell,
            # or belongs to the piece. Matching by piece color/kind and from_pos is most precise.
            if (move.from_pos == piece_view.cell and 
                    move.piece.color == piece_view.color and 
                    move.piece.kind == piece_view.kind):
                active_move = move
                break

        # If there is no active move in the snapshot for this piece anymore, it has finished or cancelled.
        if active_move is None:
            # Reached destination, transition to next state (cooldown/long_rest)
            next_state = self.config.get("physics", {}).get("next_state_when_finished", "long_rest")
            piece_view.change_state(next_state, snapshot)
            return

        # 2. Determine progress based strictly on time difference (no game logic duplication)
        duration = self.arrival - self.start_clock
        if duration <= 0:
            duration = 1000

        current_clock = snapshot.clock
        if current_clock >= self.arrival:
            progress = 1.0
        else:
            progress = max(0.0, (current_clock - self.start_clock) / duration)

        # 3. Interpolate coordinates along the path
        path = active_move.path
        n_cells = len(path)
        if n_cells <= 1:
            # Fail-safe: draw at destination
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

        # 4. Check if finished
        if progress >= 1.0:
            # Update logical cell coordinates on the view
            piece_view.cell = active_move.to_pos
            next_state = self.config.get("physics", {}).get("next_state_when_finished", "long_rest")
            piece_view.change_state(next_state, snapshot)
