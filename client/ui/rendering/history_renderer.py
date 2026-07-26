import cv2
import client.ui.ui_config as cfg
from client.ui.rendering.img import Img
from shared.models.game_snapshot import GameSnapshot
from client.services.score_tracker import ScoreTracker
from shared.models.color import Color

FORMAT_TIME_TEMPLATE = "{:02d}:{:02d}.{:03d}"
FORMAT_ALGEBRAIC_TEMPLATE = "{}{}"
PIECE_KING_CHAR = "K"
PIECE_PAWN_CHAR = "P"
NOTATION_CASTLE_SHORT = "O-O"
NOTATION_CASTLE_LONG = "O-O-O"
PANEL_TITLE_WHITE = "WHITE MOVES"
PANEL_TITLE_BLACK = "BLACK MOVES"
PANEL_SCORE_WHITE_PREFIX = "White"
PANEL_SCORE_BLACK_PREFIX = "Black"
HEADER_TIME = "Time"
HEADER_MOVE = "Move"

def format_time(ms: int) -> str:
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return FORMAT_TIME_TEMPLATE.format(minutes, seconds, milliseconds)

def format_move_notation(record, board_height: int) -> str:
    def cell_to_alg(cell) -> str:
        file_char = chr(ord('a') + cell.x)
        rank_num = board_height - cell.y
        return FORMAT_ALGEBRAIC_TEMPLATE.format(file_char, rank_num)

    if 'to_pos' not in record:
        return ""
    to_str = cell_to_alg(record['to_pos'])
    kind = record['kind']
    
    if kind == PIECE_KING_CHAR and 'from_pos' in record and record['from_pos'] is not None:
        if abs(record['from_pos'].x - record['to_pos'].x) == 2:
            if record['to_pos'].x > record['from_pos'].x:
                return NOTATION_CASTLE_SHORT
            else:
                return NOTATION_CASTLE_LONG

    if kind == PIECE_PAWN_CHAR:
        if record.get('is_capture', False) and 'from_pos' in record and record['from_pos'] is not None:
            dep_file = chr(ord('a') + record['from_pos'].x)
            return f"{dep_file}x{to_str}"
        else:
            return to_str
    else:
        if record.get('is_capture', False):
            return f"{kind}x{to_str}"
        else:
            return f"{kind}{to_str}"

class HistoryRenderer:
    def __init__(self, history_tracker=None, left_padding: int = 0, right_padding: int = 0, score_tracker=None):
        self.history_tracker = history_tracker
        self.left_padding = left_padding
        self.right_padding = right_padding
        self.score_tracker = score_tracker or ScoreTracker()

    def draw_history_panels(self, canvas: Img, snapshot: GameSnapshot, board_w: int, board_h: int, total_w: int) -> None:
        """Draws White and Black Move History Columns in the padded areas if available."""
        if self.score_tracker.pubsub is None:
            self.score_tracker.update(snapshot)

        if self.left_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, PANEL_TITLE_WHITE, Color.WHITE, cfg.HIST_PANEL_PADDING, self.left_padding - cfg.HIST_PANEL_PADDING, board_h, snapshot)
        
        if self.right_padding > 0 and self.history_tracker:
            self._draw_history_panel(canvas, PANEL_TITLE_BLACK, Color.BLACK, self.left_padding + board_w + cfg.HIST_PANEL_PADDING, total_w - cfg.HIST_PANEL_PADDING, board_h, snapshot)

    def _draw_history_panel(self, canvas: Img, title: str, color: str, x_start: int, x_end: int, board_h: int, snapshot: GameSnapshot) -> None:
        cv2.rectangle(canvas.img, (x_start, cfg.HIST_PANEL_Y_MARGIN), (x_end, board_h - cfg.HIST_PANEL_Y_MARGIN), cfg.BG_COLOR_BGR, -1)

        title_y_start = cfg.HIST_PANEL_Y_MARGIN + 10
        title_y_end = title_y_start + 35
        title_box_margin = 25
        title_x_start = x_start + title_box_margin
        title_x_end = x_end - title_box_margin
        
        cv2.rectangle(canvas.img, (title_x_start, title_y_start), (title_x_end, title_y_end), (255, 255, 255), -1)
        cv2.rectangle(canvas.img, (title_x_start, title_y_start), (title_x_end, title_y_end), (200, 200, 200), 1)
        
        score = self.score_tracker.get_score(color)
        display_title = f"{PANEL_SCORE_WHITE_PREFIX if color == Color.WHITE else PANEL_SCORE_BLACK_PREFIX} ({score})"
        
        (w, h), _ = cv2.getTextSize(display_title, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        title_x = title_x_start + (title_x_end - title_x_start - w) // 2
        title_y = title_y_start + (title_y_end - title_y_start + h) // 2
        canvas.put_text(display_title, title_x, title_y, 0.45, (80, 80, 80), 1)

        # Table area
        table_y_start = title_y_end + 15
        table_y_end = board_h - cfg.HIST_PANEL_Y_MARGIN - 10
        table_x_start = x_start + 10
        table_x_end = x_end - 10
        table_w = table_x_end - table_x_start
        
        cv2.rectangle(canvas.img, (table_x_start, table_y_start), (table_x_end, table_y_end), (255, 255, 255), -1)
        cv2.rectangle(canvas.img, (table_x_start, table_y_start), (table_x_end, table_y_end), (200, 200, 200), 1)

        header_height = 25
        header_line_y = table_y_start + header_height
        cv2.line(canvas.img, (table_x_start, header_line_y), (table_x_end, header_line_y), (220, 220, 220), 1)
        
        sep_x = table_x_start + int(table_w * 0.45)
        cv2.line(canvas.img, (sep_x, table_y_start), (sep_x, table_y_end), (220, 220, 220), 1)

        left_col_w = sep_x - table_x_start
        right_col_w = table_x_end - sep_x

        (tw, th), _ = cv2.getTextSize(HEADER_TIME, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        time_x = table_x_start + (left_col_w - tw) // 2
        canvas.put_text(HEADER_TIME, time_x, table_y_start + 17, 0.4, (80, 80, 80), 1)

        (mw, mh), _ = cv2.getTextSize(HEADER_MOVE, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        move_x = sep_x + (right_col_w - mw) // 2
        canvas.put_text(HEADER_MOVE, move_x, table_y_start + 17, 0.4, (80, 80, 80), 1)

        moves = [m for m in self.history_tracker.history if m['color'] == color]
        row_height = 25
        max_moves = (table_y_end - header_line_y) // row_height
        visible_moves = moves[-max_moves:] if len(moves) > max_moves else moves

        for idx, m in enumerate(visible_moves):
            curr_row_y = header_line_y + idx * row_height
            next_row_y = curr_row_y + row_height
            
            if idx < len(visible_moves) - 1:
                cv2.line(canvas.img, (table_x_start, next_row_y), (table_x_end, next_row_y), (240, 240, 240), 1)
                
            time_str = format_time(m['time'])
            move_str = format_move_notation(m, snapshot.board.height)

            (tw, th), _ = cv2.getTextSize(time_str, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
            tx = table_x_start + (left_col_w - tw) // 2
            canvas.put_text(time_str, tx, curr_row_y + 17, 0.38, (120, 120, 120), 1)

            (mw, mh), _ = cv2.getTextSize(move_str, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
            mx = sep_x + (right_col_w - mw) // 2
            canvas.put_text(move_str, mx, curr_row_y + 17, 0.38, (50, 50, 50), 1)



