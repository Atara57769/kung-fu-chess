import numpy as np
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.board.board_geometry import BoardGeometry

class Renderer:
    def __init__(self, asset_loader, geometry: BoardGeometry, history_tracker=None, left_padding: int = 0, right_padding: int = 0):
        self.asset_loader = asset_loader
        self.geometry = geometry
        self.history_tracker = history_tracker
        self.left_padding = left_padding
        self.right_padding = right_padding

    def render(self, snapshot: GameSnapshot, active_views: list) -> Img:
        """Assembles the current visual frame onto a canvas Img."""
        # 1. Load the background image to get original dimensions
        bg_img = self.asset_loader.get_board_background()
        board_h, board_w, board_c = bg_img.img.shape
        total_w = board_w + self.left_padding + self.right_padding

        # 2. Create canvas with extra padding on left and right, filled with clean dark background
        canvas = Img()
        canvas.img = np.zeros((board_h, total_w, board_c), dtype=np.uint8)
        if board_c == 4:
            canvas.img[:] = (27, 26, 24, 255)  # Hex #181a1b charcoal BGRA
        else:
            canvas.img[:] = (27, 26, 24)  # Hex #181a1b charcoal BGR

        # 3. Draw the board background shifted by left_padding
        canvas.img[:, self.left_padding:self.left_padding + board_w] = bg_img.img

        # 4. Draw all active pieces offset by left_padding
        for view in active_views:
            sprite = view.get_sprite()
            # Draw sprite frame on canvas at its visual coordinates (px + left_padding, py)
            sprite.draw_on(canvas, view.px + self.left_padding, view.py)

            # Check if this piece is selected in the game snapshot
            is_selected = (snapshot.selected_piece is not None and 
                           snapshot.selected_piece.cell == view.cell and 
                           snapshot.selected_piece.color == view.color and 
                           snapshot.selected_piece.kind == view.kind)

            if is_selected:
                # Overlay selection indicator
                canvas.put_text("SEL", view.px + self.left_padding + 5, view.py + 25, 0.6, (0, 255, 255, 255), 2)

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
                canvas.put_text(f"{remaining_ms}ms", view.px + self.left_padding + 5, view.py + 85, 0.5, (0, 0, 255, 255), 2)

        # 5. Draw White and Black Move History Columns
        if self.left_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "WHITE MOVES", 'w', 10, self.left_padding - 10, board_h, snapshot.board.height)
        
        if self.right_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "BLACK MOVES", 'b', self.left_padding + board_w + 10, total_w - 10, board_h, snapshot.board.height)

        if snapshot.game_over:
            text_x = self.left_padding + board_w // 2 - 200
            canvas.put_text("GAME OVER", text_x, board_h // 2, 2.0, (0, 0, 255, 255), 4)

        return canvas

    def _draw_history_panel(self, canvas, title: str, color: str, x_start: int, x_end: int, board_h: int, board_height: int) -> None:
        import cv2
        # Draw background card
        cv2.rectangle(canvas.img, (x_start, 20), (x_end, board_h - 20), (36, 34, 31), -1) # filled
        cv2.rectangle(canvas.img, (x_start, 20), (x_end, board_h - 20), (66, 63, 58), 2) # border

        # Draw Title
        title_x = x_start + (x_end - x_start) // 2 - 60
        text_color = (220, 220, 220, 255) if color == 'w' else (255, 180, 100, 255)
        canvas.put_text(title, title_x, 50, 0.6, text_color, 2)

        # Draw divider line
        cv2.line(canvas.img, (x_start + 10, 65), (x_end - 10, 65), (66, 63, 58), 1)

        # Filter moves
        moves = [m for m in self.history_tracker.history if m['color'] == color]
        
        # Calculate how many moves can fit
        y_start = 95
        y_step = 28
        y_end = board_h - 40
        max_visible = (y_end - y_start) // y_step

        visible_moves = moves[-max_visible:] if len(moves) > max_visible else moves

        piece_names = {
            'P': 'Pawn',
            'N': 'Knight',
            'B': 'Bishop',
            'R': 'Rook',
            'Q': 'Queen',
            'K': 'King'
        }

        def cell_to_algebraic(cell) -> str:
            file_char = chr(ord('a') + cell.x)
            rank_num = board_height - cell.y
            return f"{file_char}{rank_num}"

        # Draw moves
        for idx, m in enumerate(visible_moves):
            y_pos = y_start + idx * y_step
            p_name = piece_names.get(m['kind'], m['kind'])
            to_str = cell_to_algebraic(m['to_pos'])
            move_text = f"{m['time']}ms: {p_name} to {to_str}"
            canvas.put_text(move_text, x_start + 15, y_pos, 0.55, (200, 200, 200, 255), 1)
