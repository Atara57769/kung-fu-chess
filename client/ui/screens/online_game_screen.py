import cv2
import numpy as np
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen
from client.ui.components.button import Button
from client.ui.ui_config import (
    BG_COLOR_BGR, GAMEOVER_FONT_SCALE, GAMEOVER_COLOR, GAMEOVER_THICKNESS
)


class OnlineGameScreen(Screen):
    """Presents the active online game board, handles local selections, and replicates server snapshots."""
    
    def __init__(self, screen_manager, client, geometry, renderer, animation_manager, history_tracker=None) -> None:
        self.screen_manager = screen_manager
        self.client = client
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.history_tracker = history_tracker or getattr(renderer, "history_tracker", None)

    def _get_cell_from_coordinates(self, x: int, y: int) -> any:
        """Translates pixel coordinates to board cell taking left padding into account."""
        board_x = x - self.renderer.left_padding
        return self.geometry.pixel_to_cell(board_x, y)

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Translates mouse coordinates to cells and requests click/jump from the server."""
        if self.client.game_over_result is not None:
            self._exit_to_home()
            return
            
        cell = self._get_cell_from_coordinates(x, y)
        if cell is None:
            return

        snapshot = self.client.current_snapshot
        if snapshot is None:
            return

        if is_right:
            self.client.send_jump(cell)
        else:
            self.client.send_click(cell)

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
            msg = self.client.countdown_message or f"Opponent disconnected. Autoresign in {self.client.countdown_seconds}s"
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
            
            # Winner Announcement
            winner = result.get("winner", "draw").upper()
            announcement = f"GAME OVER - {winner} WINS" if winner != "DRAW" else "GAME OVER - DRAW"
            canvas.put_text(announcement, width // 2 - 200, by + 50, font_size=0.8, color=(0, 0, 255), thickness=3)
            
            # Rating change
            change_w = result.get("white_rating_change", "")
            change_b = result.get("black_rating_change", "")
            details = f"White: {change_w}  |  Black: {change_b}"
            canvas.put_text(details, width // 2 - 220, by + 95, font_size=0.5, color=(200, 200, 200), thickness=1)
            
            canvas.put_text("Click anywhere to return to Home", width // 2 - 160, by + 135, font_size=0.45, color=(150, 240, 150), thickness=1)

    def render(self, canvas: Img) -> None:
        """Overrides selection and renders server-snapshot on screen canvas."""
        snapshot = self.client.current_snapshot
        if snapshot is None:
            if canvas.img is None:
                canvas.img = np.zeros((self.geometry.cell_size * 8, self.geometry.cell_size * 8 + 500, 3), dtype=np.uint8)
            canvas.img[:] = BG_COLOR_BGR
            canvas.put_text("Waiting for server state...", 100, 100, 0.6, (200, 200, 200), 2)
            return

        rendered_canvas = self.renderer.render(snapshot, self.animation_manager.active_views)
        canvas.img = rendered_canvas.img
        
        h, w = canvas.img.shape[:2]
        self._draw_disconnect_countdown(canvas, w, h)
        self._draw_game_over_banner(canvas, w, h)
