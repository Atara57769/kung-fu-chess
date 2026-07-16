import numpy as np
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.board.board_geometry import BoardGeometry
from ui.ui_config import (
    BG_COLOR_BGR, BG_COLOR_BGRA,
    SEL_TEXT, SEL_OFFSET_X, SEL_OFFSET_Y, SEL_FONT_SCALE, SEL_COLOR, SEL_THICKNESS,
    COOLDOWN_OFFSET_X, COOLDOWN_OFFSET_Y, COOLDOWN_FONT_SCALE, COOLDOWN_COLOR, COOLDOWN_THICKNESS,
    HIST_PANEL_BG_COLOR, HIST_PANEL_BORDER_COLOR, HIST_PANEL_BORDER_THICKNESS, HIST_PANEL_PADDING,
    HIST_PANEL_Y_MARGIN,
    HIST_TITLE_Y, HIST_TITLE_FONT_SCALE, HIST_TITLE_THICKNESS, HIST_TITLE_X_OFFSET,
    HIST_TITLE_COLOR_WHITE, HIST_TITLE_COLOR_BLACK,
    HIST_DIVIDER_Y, HIST_DIVIDER_COLOR, HIST_DIVIDER_THICKNESS,
    HIST_MOVE_Y_START, HIST_MOVE_Y_STEP, HIST_MOVE_Y_PADDING,
    HIST_MOVE_TEXT_X_OFFSET, HIST_MOVE_FONT_SCALE, HIST_MOVE_COLOR, HIST_MOVE_THICKNESS,
    GAMEOVER_TEXT, GAMEOVER_X_OFFSET, GAMEOVER_FONT_SCALE, GAMEOVER_COLOR, GAMEOVER_THICKNESS
)

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
        canvas = self._create_canvas(board_w, board_h, board_c, total_w)

        # 3. Draw the board background shifted by left_padding
        self._draw_board_background(canvas, bg_img, board_w)

        # 4. Draw all active pieces and overlays offset by left_padding
        self._draw_pieces(canvas, snapshot, active_views)

        # 5. Draw White and Black Move History Columns
        self._draw_history_panels(canvas, snapshot, board_w, board_h, total_w)

        # 6. Draw Game Over text if the game is over
        if snapshot.game_over:
            self._draw_game_over(canvas, board_w, board_h)

        return canvas

    def _create_canvas(self, board_w: int, board_h: int, board_c: int, total_w: int) -> Img:
        """Creates the canvas with extra padding on left and right, filled with clean dark background."""
        canvas = Img()
        canvas.img = np.zeros((board_h, total_w, board_c), dtype=np.uint8)
        if board_c == 4:
            canvas.img[:] = BG_COLOR_BGRA
        else:
            canvas.img[:] = BG_COLOR_BGR
        return canvas

    def _draw_board_background(self, canvas: Img, bg_img: Img, board_w: int) -> None:
        """Draws the board background shifted by left_padding."""
        canvas.img[:, self.left_padding:self.left_padding + board_w] = bg_img.img

    def _draw_pieces(self, canvas: Img, snapshot: GameSnapshot, active_views: list) -> None:
        """Draws all active pieces and their selection/cooldown overlays."""
        for view in active_views:
            sprite = view.get_sprite()
            # Draw sprite frame on canvas at its visual coordinates (px + left_padding, py)
            sprite.draw_on(canvas, view.px + self.left_padding, view.py)

            self._draw_piece_selection_overlay(canvas, snapshot, view)
            self._draw_piece_cooldown_overlay(canvas, snapshot, view)

    def _draw_piece_selection_overlay(self, canvas: Img, snapshot: GameSnapshot, view) -> None:
        """Overlay selection indicator if this piece is selected."""
        is_selected = (snapshot.selected_piece is not None and 
                       snapshot.selected_piece.cell == view.cell and 
                       snapshot.selected_piece.color == view.color and 
                       snapshot.selected_piece.kind == view.kind)

        if is_selected:
            canvas.put_text(
                SEL_TEXT,
                view.px + self.left_padding + SEL_OFFSET_X,
                view.py + SEL_OFFSET_Y,
                SEL_FONT_SCALE,
                SEL_COLOR,
                SEL_THICKNESS
            )

    def _draw_piece_cooldown_overlay(self, canvas: Img, snapshot: GameSnapshot, view) -> None:
        """Overlay remaining cooldown in milliseconds if active."""
        # Find matching PieceSnapshot to check for active cooldown overlay
        piece_snap = None
        for row in snapshot.board.grid:
            for p in row:
                if p is not None and p.color == view.color and p.kind == view.kind and p.cell == view.cell:
                    piece_snap = p
                    break

        if piece_snap and piece_snap.cooldown_until > snapshot.clock:
            remaining_ms = piece_snap.cooldown_until - snapshot.clock
            canvas.put_text(
                f"{remaining_ms}ms",
                view.px + self.left_padding + COOLDOWN_OFFSET_X,
                view.py + COOLDOWN_OFFSET_Y,
                COOLDOWN_FONT_SCALE,
                COOLDOWN_COLOR,
                COOLDOWN_THICKNESS
            )

    def _draw_history_panels(self, canvas: Img, snapshot: GameSnapshot, board_w: int, board_h: int, total_w: int) -> None:
        """Draw White and Black Move History Columns."""
        if self.left_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "WHITE MOVES", 'w', HIST_PANEL_PADDING, self.left_padding - HIST_PANEL_PADDING, board_h, snapshot.board.height)
        
        if self.right_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "BLACK MOVES", 'b', self.left_padding + board_w + HIST_PANEL_PADDING, total_w - HIST_PANEL_PADDING, board_h, snapshot.board.height)

    def _draw_game_over(self, canvas: Img, board_w: int, board_h: int) -> None:
        """Draw Game Over banner on the canvas."""
        text_x = self.left_padding + board_w // 2 + GAMEOVER_X_OFFSET
        canvas.put_text(GAMEOVER_TEXT, text_x, board_h // 2, GAMEOVER_FONT_SCALE, GAMEOVER_COLOR, GAMEOVER_THICKNESS)

    def _draw_history_panel(self, canvas, title: str, color: str, x_start: int, x_end: int, board_h: int, board_height: int) -> None:
        import cv2
        # Draw background card
        cv2.rectangle(canvas.img, (x_start, HIST_PANEL_Y_MARGIN), (x_end, board_h - HIST_PANEL_Y_MARGIN), HIST_PANEL_BG_COLOR, -1) # filled
        cv2.rectangle(canvas.img, (x_start, HIST_PANEL_Y_MARGIN), (x_end, board_h - HIST_PANEL_Y_MARGIN), HIST_PANEL_BORDER_COLOR, HIST_PANEL_BORDER_THICKNESS) # border

        # Draw Title
        title_x = x_start + (x_end - x_start) // 2 - HIST_TITLE_X_OFFSET
        text_color = HIST_TITLE_COLOR_WHITE if color == 'w' else HIST_TITLE_COLOR_BLACK
        canvas.put_text(title, title_x, HIST_TITLE_Y, HIST_TITLE_FONT_SCALE, text_color, HIST_TITLE_THICKNESS)

        # Draw divider line
        cv2.line(canvas.img, (x_start + HIST_PANEL_PADDING, HIST_DIVIDER_Y), (x_end - HIST_PANEL_PADDING, HIST_DIVIDER_Y), HIST_DIVIDER_COLOR, HIST_DIVIDER_THICKNESS)

        # Filter moves
        moves = [m for m in self.history_tracker.history if m['color'] == color]
        
        # Calculate how many moves can fit
        y_start = HIST_MOVE_Y_START
        y_step = HIST_MOVE_Y_STEP
        y_end = board_h - HIST_MOVE_Y_PADDING
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
            canvas.put_text(move_text, x_start + HIST_MOVE_TEXT_X_OFFSET, y_pos, HIST_MOVE_FONT_SCALE, HIST_MOVE_COLOR, HIST_MOVE_THICKNESS)
