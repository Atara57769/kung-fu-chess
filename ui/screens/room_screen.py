import cv2
import numpy as np
from ui.rendering.img import Img
from ui.screens.base_screen import Screen
from ui.components.button import Button
from ui.components.label import Label
from ui.ui_config import BG_COLOR_BGR

class RoomScreen(Screen):
    """Lobby screen for custom chess rooms showing players, spectators, and start trigger."""
    
    def __init__(self, screen_manager, width: int, height: int, room_id: str, 
                 is_creator: bool = False, white_player: str = None, black_player: str = None) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        self.room_id = room_id
        self.is_creator = is_creator
        
        self.white_player = white_player or "[Empty]"
        self.black_player = black_player or "[Empty]"
        self.spectators: list[str] = []
        
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        
        self._setup_components()

    def _setup_components(self) -> None:
        """Initializes labels and control buttons based on player status/role."""
        cx = self.width // 2
        
        # Header Info
        self.labels.append(Label(cx, 80, f"LOBBY - ROOM {self.room_id}", centered=True))
        
        # Seating Information Labels
        self.labels.append(Label(cx - 150, 150, f"White Seat: {self.white_player}"))
        self.labels.append(Label(cx - 150, 190, f"Black Seat: {self.black_player}"))
        self.labels.append(Label(cx - 150, 230, "Spectators: None"))
        
        # Lobby Actions
        if self.is_creator:
            self.buttons.append(Button(cx - 180, 300, 160, 45, "Start Game", self._on_start_game))
            self.buttons.append(Button(cx + 20, 300, 160, 45, "Leave Lobby", self._on_leave_lobby))
        else:
            self.buttons.append(Button(cx - 80, 300, 160, 45, "Leave Lobby", self._on_leave_lobby))

    def _on_start_game(self) -> None:
        """Transition simulation to GameScreen for offline testing purposes."""
        print(f"[Lobby] Starting room {self.room_id} game offline...")
        # Offline fallback: Transition to local GameScreen if we want to run/test UI directly.
        # Online client will override this button callback to request a start from the server.

    def _on_leave_lobby(self) -> None:
        """Returns to the home screen."""
        from ui.screens.home_screen import HomeScreen
        home_screen = HomeScreen(self.screen_manager, self.width, self.height)
        self.screen_manager.switch_to(home_screen)

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Processes clicks on buttons."""
        for btn in self.buttons:
            btn.handle_click(x, y)

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Updates hover state on buttons."""
        for btn in self.buttons:
            btn.update_hover(x, y)

    def update(self, dt: float) -> None:
        """Lobby update ticks (e.g. heartbeat or poll)."""
        pass

    def _draw_gradient_background(self, canvas: Img) -> None:
        """Fills canvas with a sleek dark radial-like vertical gradient."""
        c1 = np.array([25, 23, 21], dtype=np.float32)
        c2 = np.array([12, 10, 8], dtype=np.float32)
        
        for y in range(self.height):
            factor = y / self.height
            color = (1.0 - factor) * c1 + factor * c2
            canvas.img[y, :] = color.astype(np.uint8)

    def render(self, canvas: Img) -> None:
        """Renders the background, seating statuses, spectator lists, and buttons."""
        if canvas.img is None:
            canvas.img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
        self._draw_gradient_background(canvas)
        
        for lbl in self.labels:
            lbl.render(canvas)
            
        for btn in self.buttons:
            btn.render(canvas)
