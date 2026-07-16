import cv2
import ui.ui_config as cfg
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.rendering.score_tracker import ScoreTracker
from constants import COLOR_WHITE, COLOR_BLACK

class HistoryRenderer:
    def __init__(self, history_tracker=None, left_padding: int = 0, right_padding: int = 0, score_tracker=None):
        self.history_tracker = history_tracker
        self.left_padding = left_padding
        self.right_padding = right_padding
        self.score_tracker = score_tracker or ScoreTracker()

    def draw_history_panels(self, canvas: Img, snapshot: GameSnapshot, board_w: int, board_h: int, total_w: int) -> None:
        """Draws White and Black Move History Columns in the padded areas if available."""
        self.score_tracker.update(snapshot)

        if self.left_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "WHITE MOVES", COLOR_WHITE, cfg.HIST_PANEL_PADDING, self.left_padding - cfg.HIST_PANEL_PADDING, board_h, snapshot)
        
        if self.right_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, "BLACK MOVES", COLOR_BLACK, self.left_padding + board_w + cfg.HIST_PANEL_PADDING, total_w - cfg.HIST_PANEL_PADDING, board_h, snapshot)

    def _draw_history_panel(self, canvas: Img, title: str, color: str, x_start: int, x_end: int, board_h: int, snapshot: GameSnapshot) -> None:
        cv2.rectangle(canvas.img, (x_start, cfg.HIST_PANEL_Y_MARGIN), (x_end, board_h - cfg.HIST_PANEL_Y_MARGIN), cfg.HIST_PANEL_BG_COLOR, -1) # filled
        cv2.rectangle(canvas.img, (x_start, cfg.HIST_PANEL_Y_MARGIN), (x_end, board_h - cfg.HIST_PANEL_Y_MARGIN), cfg.HIST_PANEL_BORDER_COLOR, cfg.HIST_PANEL_BORDER_THICKNESS) # border

        # Retrieve player score from ScoreTracker
        score = self.score_tracker.get_score(color)
        display_title = f"{title} ({score})"

        (w, h), _ = cv2.getTextSize(display_title, cv2.FONT_HERSHEY_SIMPLEX, cfg.HIST_TITLE_FONT_SCALE, cfg.HIST_TITLE_THICKNESS)
        title_x = x_start + (x_end - x_start - w) // 2
        text_color = cfg.HIST_TITLE_COLOR_WHITE if color == COLOR_WHITE else cfg.HIST_TITLE_COLOR_BLACK
        canvas.put_text(display_title, title_x, cfg.HIST_TITLE_Y, cfg.HIST_TITLE_FONT_SCALE, text_color, cfg.HIST_TITLE_THICKNESS)

        cv2.line(canvas.img, (x_start + cfg.HIST_PANEL_PADDING, cfg.HIST_DIVIDER_Y), (x_end - cfg.HIST_PANEL_PADDING, cfg.HIST_DIVIDER_Y), cfg.HIST_DIVIDER_COLOR, cfg.HIST_DIVIDER_THICKNESS)

        moves = [m for m in self.history_tracker.history if m['color'] == color]
        
        y_start = cfg.HIST_MOVE_Y_START
        y_step = cfg.HIST_MOVE_Y_STEP
        y_end = board_h - cfg.HIST_MOVE_Y_PADDING
        max_visible = (y_end - y_start) // y_step

        visible_moves = moves[-max_visible:] if len(moves) > max_visible else moves

        def cell_to_algebraic(cell) -> str:
            file_char = chr(ord('a') + cell.x)
            rank_num = snapshot.board.height - cell.y
            return f"{file_char}{rank_num}"

        for idx, m in enumerate(visible_moves):
            y_pos = y_start + idx * y_step
            p_token = m['kind']
            to_str = cell_to_algebraic(m['to_pos'])
            move_text = f"{m['time']}ms: {p_token} to {to_str}"
            canvas.put_text(move_text, x_start + cfg.HIST_MOVE_TEXT_X_OFFSET, y_pos, cfg.HIST_MOVE_FONT_SCALE, cfg.HIST_MOVE_COLOR, cfg.HIST_MOVE_THICKNESS)


