import cv2
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.ui_config import (
    HIST_PANEL_BG_COLOR, HIST_PANEL_BORDER_COLOR, HIST_PANEL_BORDER_THICKNESS, HIST_PANEL_PADDING,
    HIST_PANEL_Y_MARGIN,
    HIST_TITLE_Y, HIST_TITLE_FONT_SCALE, HIST_TITLE_THICKNESS, HIST_TITLE_X_OFFSET,
    HIST_TITLE_COLOR_WHITE, HIST_TITLE_COLOR_BLACK,
    HIST_DIVIDER_Y, HIST_DIVIDER_COLOR, HIST_DIVIDER_THICKNESS,
    HIST_MOVE_Y_START, HIST_MOVE_Y_STEP, HIST_MOVE_Y_PADDING,
    HIST_MOVE_TEXT_X_OFFSET, HIST_MOVE_FONT_SCALE, HIST_MOVE_COLOR, HIST_MOVE_THICKNESS,
    PIECE_POINTS
)

class HistoryRenderer:
    def __init__(self, history_tracker=None, left_padding: int = 0, right_padding: int = 0):
        self.history_tracker = history_tracker
        self.left_padding = left_padding
        self.right_padding = right_padding

    def draw_history_panels(self, canvas: Img, snapshot: GameSnapshot, board_w: int, board_h: int, total_w: int) -> None:
        """Draws White and Black Move History Columns in the padded areas if available."""
        if self.left_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "WHITE MOVES", 'w', HIST_PANEL_PADDING, self.left_padding - HIST_PANEL_PADDING, board_h, snapshot)
        
        if self.right_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "BLACK MOVES", 'b', self.left_padding + board_w + HIST_PANEL_PADDING, total_w - HIST_PANEL_PADDING, board_h, snapshot)

    def _draw_history_panel(self, canvas: Img, title: str, color: str, x_start: int, x_end: int, board_h: int, snapshot: GameSnapshot) -> None:
        cv2.rectangle(canvas.img, (x_start, HIST_PANEL_Y_MARGIN), (x_end, board_h - HIST_PANEL_Y_MARGIN), HIST_PANEL_BG_COLOR, -1) # filled
        cv2.rectangle(canvas.img, (x_start, HIST_PANEL_Y_MARGIN), (x_end, board_h - HIST_PANEL_Y_MARGIN), HIST_PANEL_BORDER_COLOR, HIST_PANEL_BORDER_THICKNESS) # border

        # Calculate player score from snapshot
        score = sum(
            PIECE_POINTS.get(piece.kind, 0)
            for row in snapshot.board.grid
            for piece in row
            if piece is not None and piece.color == color
        )
        display_title = f"{title} ({score})"

        (w, h), _ = cv2.getTextSize(display_title, cv2.FONT_HERSHEY_SIMPLEX, HIST_TITLE_FONT_SCALE, HIST_TITLE_THICKNESS)
        title_x = x_start + (x_end - x_start - w) // 2
        text_color = HIST_TITLE_COLOR_WHITE if color == 'w' else HIST_TITLE_COLOR_BLACK
        canvas.put_text(display_title, title_x, HIST_TITLE_Y, HIST_TITLE_FONT_SCALE, text_color, HIST_TITLE_THICKNESS)

        cv2.line(canvas.img, (x_start + HIST_PANEL_PADDING, HIST_DIVIDER_Y), (x_end - HIST_PANEL_PADDING, HIST_DIVIDER_Y), HIST_DIVIDER_COLOR, HIST_DIVIDER_THICKNESS)

        moves = [m for m in self.history_tracker.history if m['color'] == color]
        
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
            rank_num = snapshot.board.height - cell.y
            return f"{file_char}{rank_num}"

        for idx, m in enumerate(visible_moves):
            y_pos = y_start + idx * y_step
            p_name = piece_names.get(m['kind'], m['kind'])
            to_str = cell_to_algebraic(m['to_pos'])
            move_text = f"{m['time']}ms: {p_name} to {to_str}"
            canvas.put_text(move_text, x_start + HIST_MOVE_TEXT_X_OFFSET, y_pos, HIST_MOVE_FONT_SCALE, HIST_MOVE_COLOR, HIST_MOVE_THICKNESS)

