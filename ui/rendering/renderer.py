import numpy as np
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.board.board_geometry import BoardGeometry
from ui.rendering.history_renderer import HistoryRenderer
from constants import CELL_SIZE
from ui.ui_config import (
    BG_COLOR_BGR, BG_COLOR_BGRA,
    SEL_TEXT, SEL_OFFSET_X, SEL_OFFSET_Y, SEL_FONT_SCALE, SEL_COLOR, SEL_THICKNESS,
    COOLDOWN_OFFSET_X, COOLDOWN_OFFSET_Y, COOLDOWN_FONT_SCALE, COOLDOWN_COLOR, COOLDOWN_THICKNESS,
    GAMEOVER_TEXT, GAMEOVER_X_OFFSET, GAMEOVER_FONT_SCALE, GAMEOVER_COLOR, GAMEOVER_THICKNESS
)

class Renderer:
    def __init__(self, asset_loader, geometry: BoardGeometry, history_tracker=None, left_padding: int = 0, right_padding: int = 0, score_tracker=None):
        self.asset_loader = asset_loader
        self.geometry = geometry
        self.history_tracker = history_tracker
        self.left_padding = left_padding
        self.right_padding = right_padding
        self.history_renderer = HistoryRenderer(history_tracker, left_padding, right_padding, score_tracker)

    def _get_scale_ratio(self) -> float:
        return self.geometry.cell_size / CELL_SIZE

    def render(self, snapshot: GameSnapshot, active_views: list) -> Img:
        """Assembles the current visual frame onto a canvas Img."""
        bg_img = self.asset_loader.get_board_background()
        board_h, board_w, board_c = bg_img.img.shape
        total_w = board_w + self.left_padding + self.right_padding

        canvas = self._create_canvas(board_w, board_h, board_c, total_w)

        self._draw_board_background(canvas, bg_img, board_w)

        self._draw_pieces(canvas, snapshot, active_views)

        self._draw_history_panels(canvas, snapshot, board_w, board_h, total_w)

        if snapshot.game_over:
            self._draw_game_over(canvas, board_w, board_h)

        return canvas

    def _create_canvas(self, board_w: int, board_h: int, board_c: int, total_w: int) -> Img:
        canvas = Img()
        canvas.img = np.zeros((board_h, total_w, board_c), dtype=np.uint8)
        if board_c == 4:
            canvas.img[:] = BG_COLOR_BGRA
        else:
            canvas.img[:] = BG_COLOR_BGR
        return canvas

    def _draw_board_background(self, canvas: Img, bg_img: Img, board_w: int) -> None:
        canvas.img[:, self.left_padding:self.left_padding + board_w] = bg_img.img

    def _draw_pieces(self, canvas: Img, snapshot: GameSnapshot, active_views: list) -> None:
        """Draws all active pieces and their selection/cooldown overlays."""
        for view in active_views:
            sprite = view.get_sprite()
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
            scale_ratio = self._get_scale_ratio()
            canvas.put_text(
                SEL_TEXT,
                int(view.px + self.left_padding + SEL_OFFSET_X * scale_ratio),
                int(view.py + SEL_OFFSET_Y * scale_ratio),
                SEL_FONT_SCALE * scale_ratio,
                SEL_COLOR,
                max(1, int(SEL_THICKNESS * scale_ratio))
            )

    def _draw_piece_cooldown_overlay(self, canvas: Img, snapshot: GameSnapshot, view) -> None:
        """Overlay remaining cooldown in milliseconds if active."""
        piece_snap = None
        for row in snapshot.board.grid:
            for p in row:
                if p is not None and p.color == view.color and p.kind == view.kind and p.cell == view.cell:
                    piece_snap = p
                    break

        if piece_snap and piece_snap.cooldown_until > snapshot.clock:
            remaining_ms = piece_snap.cooldown_until - snapshot.clock
            scale_ratio = self._get_scale_ratio()
            canvas.put_text(
                f"{remaining_ms}ms",
                int(view.px + self.left_padding + COOLDOWN_OFFSET_X * scale_ratio),
                int(view.py + COOLDOWN_OFFSET_Y * scale_ratio),
                COOLDOWN_FONT_SCALE * scale_ratio,
                COOLDOWN_COLOR,
                max(1, int(COOLDOWN_THICKNESS * scale_ratio))
            )

    def _draw_history_panels(self, canvas: Img, snapshot: GameSnapshot, board_w: int, board_h: int, total_w: int) -> None:
        """Draw White and Black Move History Columns."""
        self.history_renderer.draw_history_panels(canvas, snapshot, board_w, board_h, total_w)

    def _draw_game_over(self, canvas: Img, board_w: int, board_h: int) -> None:
        """Draw Game Over banner on the canvas."""
        scale_ratio = self._get_scale_ratio()
        text_x = int(self.left_padding + board_w // 2 + GAMEOVER_X_OFFSET * scale_ratio)
        canvas.put_text(GAMEOVER_TEXT, text_x, board_h // 2, GAMEOVER_FONT_SCALE * scale_ratio, GAMEOVER_COLOR, max(1, int(GAMEOVER_THICKNESS * scale_ratio)))
