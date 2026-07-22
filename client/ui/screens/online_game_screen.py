import dataclasses
import cv2
import numpy as np
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen
from client.ui.components.button import Button
from client.ui.ui_config import (
    BG_COLOR_BGR, GAMEOVER_FONT_SCALE, GAMEOVER_COLOR, GAMEOVER_THICKNESS
)

DISCONNECT_COUNTDOWN_FORMAT = "Opponent disconnected. Autoresign in {}s"
LABEL_DRAW = "DRAW"
BANNER_WINS_FORMAT = "GAME OVER - {} WINS"
BANNER_DRAW = "GAME OVER - DRAW"
BANNER_DETAILS_FORMAT = "White: {}  |  Black: {}"
BANNER_SUBTEXT = "Click anywhere to return to Home"
STATUS_WAITING_FOR_SERVER = "Waiting for server state..."


class OnlineGameScreen(Screen):
    """Presents the active online game board, handles local selections, and replicates server snapshots."""
    
    def __init__(self, screen_manager, client, geometry, renderer, animation_manager, history_tracker=None) -> None:
        self.screen_manager = screen_manager
        self.client = client
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.history_tracker = history_tracker or getattr(renderer, "history_tracker", None)
        self.selected_cell = None

    def _get_cell_from_coordinates(self, x: int, y: int) -> any:
        """Translates pixel coordinates to board cell taking left padding into account."""
        board_x = x - self.renderer.left_padding
        return self.geometry.pixel_to_cell(board_x, y)

    def _handle_no_selection_state(self, cell, snapshot) -> None:
        """Handles selection logic when no piece is currently selected."""
        grid = snapshot.board.grid
        piece = grid[cell.y][cell.x]
        if piece is None:
            return

        player_color = self.client.your_color
        if player_color is None or piece.color != player_color:
            return

        self.selected_cell = cell

    def _handle_selected_state(self, cell, snapshot) -> None:
        """Handles selection and move request logic when a piece is currently selected."""
        grid = snapshot.board.grid
        piece = grid[cell.y][cell.x]
        sel_cell = self.selected_cell
        if sel_cell is None:
            return

        sel_piece = grid[sel_cell.y][sel_cell.x]

        if piece is not None and sel_piece is not None and piece.color == sel_piece.color:
            self.selected_cell = cell
            return

        self.client.send_move(sel_cell, cell)
        self.selected_cell = None

    def _handle_local_selection(self, cell) -> None:
        """Manages piece selections locally for the client color."""
        snapshot = self.client.current_snapshot
        if snapshot is None:
            return

        if not (0 <= cell.y < snapshot.board.height and 0 <= cell.x < snapshot.board.width):
            self.selected_cell = None
            return

        if self.selected_cell is None:
            self._handle_no_selection_state(cell, snapshot)
        else:
            self._handle_selected_state(cell, snapshot)

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Translates mouse coordinates to cells and requests move/jump from the server."""
        if self.client.game_over_result is not None:
            self._exit_to_home()
            return
            
        cell = self._get_cell_from_coordinates(x, y)
        if cell is None:
            self.selected_cell = None
            return

        snapshot = self.client.current_snapshot
        if snapshot is None:
            return

        if is_right:
            self.client.send_jump(cell)
        else:
            self._handle_local_selection(cell)




    def _exit_to_home(self) -> None:
        """Returns the client to the Home Screen and clears room session."""
        self.client.leave_room()
        from client.ui.screens.home_screen import HomeScreen
        home = HomeScreen(self.screen_manager, self.renderer.geometry.cell_size * 8 + 500, self.renderer.geometry.cell_size * 8, self.client.username, self.client.rating)
        self.screen_manager.switch_to(home)

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Mouse move updates if needed."""
        pass

    def update(self, dt: float) -> None:
        """Advances active piece animations based on the current authoritative server snapshot."""
        snapshot = self.client.current_snapshot
        if snapshot is None:
            return
            
        if self.history_tracker is not None:
            self.history_tracker.update(snapshot)
            
        self.animation_manager.sync_pieces(snapshot)
        self.animation_manager.update(dt, snapshot)

    def _draw_disconnect_countdown(self, canvas: Img, width: int, height: int) -> None:
        """Draws disconnect countdown text if the opponent dropped connection."""
        if self.client.countdown_seconds > 0:
            msg = self.client.countdown_message or DISCONNECT_COUNTDOWN_FORMAT.format(self.client.countdown_seconds)
            cv2.rectangle(canvas.img, (0, 0), (width, 50), (0, 0, 100), thickness=-1)
            canvas.put_text(msg, 20, 32, font_size=0.55, color=(0, 255, 255), thickness=2)

    def _draw_game_over_banner(self, canvas: Img, width: int, height: int) -> None:
        """Draws ELO result banner on game completion."""
        result = self.client.game_over_result
        if result is not None:
            banner_h = 160
            by = (height - banner_h) // 2
            cv2.rectangle(canvas.img, (0, by), (width, by + banner_h), (25, 22, 20), thickness=-1)
            cv2.rectangle(canvas.img, (0, by), (width, by + banner_h), (80, 75, 70), thickness=2)
            
            winner = result.winner_name.upper()
            announcement = BANNER_WINS_FORMAT.format(winner) if winner != LABEL_DRAW else BANNER_DRAW
            canvas.put_text(announcement, width // 2 - 200, by + 50, font_size=0.8, color=(0, 0, 255), thickness=3)
            
            change_w = result.white_rating_change
            change_b = result.black_rating_change
            details = BANNER_DETAILS_FORMAT.format(change_w, change_b)
            canvas.put_text(details, width // 2 - 220, by + 95, font_size=0.5, color=(200, 200, 200), thickness=1)
            
            canvas.put_text(BANNER_SUBTEXT, width // 2 - 160, by + 135, font_size=0.45, color=(150, 240, 150), thickness=1)

    def render(self, canvas: Img) -> None:
        """Overrides selection and renders server-snapshot on screen canvas."""
        snapshot = self.client.current_snapshot
        if snapshot is None:
            if canvas.img is None:
                canvas.img = np.zeros((self.geometry.cell_size * 8, self.geometry.cell_size * 8 + 500, 3), dtype=np.uint8)
            canvas.img[:] = BG_COLOR_BGR
            canvas.put_text(STATUS_WAITING_FOR_SERVER, 100, 100, 0.6, (200, 200, 200), 2)
            return

        if self.selected_cell is not None:
            grid = snapshot.board.grid
            if 0 <= self.selected_cell.y < snapshot.board.height and 0 <= self.selected_cell.x < snapshot.board.width:
                sel_piece = grid[self.selected_cell.y][self.selected_cell.x]
                if sel_piece is not None:
                    snapshot = dataclasses.replace(snapshot, selected_piece=sel_piece)
                else:
                    self.selected_cell = None
            else:
                self.selected_cell = None

        rendered_canvas = self.renderer.render(snapshot, self.animation_manager.active_views)
        canvas.img = rendered_canvas.img
        
        h, w = canvas.img.shape[:2]
        self._draw_disconnect_countdown(canvas, w, h)
        self._draw_game_over_banner(canvas, w, h)


