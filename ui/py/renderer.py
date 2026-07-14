import numpy as np
from img import Img
from models.game_snapshot import GameSnapshot
from ui.py.board_geometry import BoardGeometry

class Renderer:
    def __init__(self, asset_loader, geometry: BoardGeometry):
        self.asset_loader = asset_loader
        self.geometry = geometry

    def render(self, snapshot: GameSnapshot, active_views: list) -> Img:
        """Assembles the current visual frame onto a canvas Img."""
        # 1. Create a fresh canvas by copying the cached background image
        bg_img = self.asset_loader.get_board_background()
        canvas = Img()
        canvas.img = np.copy(bg_img.img)

        h, w = canvas.img.shape[:2]

        # 2. Draw all active pieces using their current state animation sprites
        for view in active_views:
            sprite = view.get_sprite()
            # Draw sprite frame on canvas at its visual coordinates (px, py)
            sprite.draw_on(canvas, view.px, view.py)

            # Check if this piece is selected in the game snapshot
            is_selected = (snapshot.selected_piece is not None and 
                           snapshot.selected_piece.cell == view.cell and 
                           snapshot.selected_piece.color == view.color and 
                           snapshot.selected_piece.kind == view.kind)

            if is_selected:
                # Overlay selection indicator
                canvas.put_text("SEL", view.px + 5, view.py + 25, 0.6, (0, 255, 255, 255), 2)

            # Find matching PieceSnapshot to check for active cooldown overlay
            piece_snap = None
            for row in snapshot.board.grid:
                for p in row:
                    if p is not None and p.color == view.color and p.kind == view.kind and p.cell == view.cell:
                        piece_snap = p
                        break

            if piece_snap and piece_snap.cooldown_until > snapshot.clock:
                remaining_ms = piece_snap.cooldown_until - snapshot.clock
                # Overlay remaining cooldown in milliseconds
                canvas.put_text(f"{remaining_ms}ms", view.px + 5, view.py + 85, 0.5, (0, 0, 255, 255), 2)

        # 3. Draw UI Text Overlay
        canvas.put_text(f"Clock: {snapshot.clock} ms", 15, 35, 0.7, (0, 255, 0, 255), 2)
        
        # Display turning / moving summaries
        pending_count = len(snapshot.pending_moves)
        jump_count = len(snapshot.jumps)
        canvas.put_text(f"Moves: {pending_count} | Jumps: {jump_count}", 15, h - 20, 0.6, (255, 255, 255, 255), 2)

        if snapshot.game_over:
            canvas.put_text("GAME OVER", w // 4, h // 2, 2.0, (0, 0, 255, 255), 4)

        return canvas
