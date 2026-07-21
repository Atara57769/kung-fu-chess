import cv2
import numpy as np
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen
from client.ui.components.button import Button
from client.ui.components.label import Label
from client.ui.ui_config import BG_COLOR_BGR

class RoomScreen(Screen):
    """Lobby screen for custom chess rooms showing players, spectators, and start trigger."""
    
    def __init__(self, screen_manager, width: int, height: int, room_id: str, 
                 is_creator: bool = False, white_player: str = None, black_player: str = None, client=None) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        self.room_id = room_id
        self.is_creator = is_creator
        self.client = client
        
        self.white_player = white_player or "[Empty]"
        self.black_player = black_player or "[Empty]"
        self.spectators: list[str] = []
        
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        
        self._setup_components()

    def _setup_components(self) -> None:
        """Initializes labels and control buttons based on player status/role."""
        cx = self.width // 2
        
        self.labels.append(Label(cx, 80, f"LOBBY - ROOM {self.room_id}", centered=True))
        
        self.labels.append(Label(cx - 150, 150, f"White Seat: {self.white_player}"))
        self.labels.append(Label(cx - 150, 190, f"Black Seat: {self.black_player}"))
        self.labels.append(Label(cx - 150, 230, "Spectators: None"))
        
        self.buttons.append(Button(cx - 80, 300, 160, 45, "Leave Lobby", self._on_leave_lobby))
      
    def _on_leave_lobby(self) -> None:
        if self.client:
            self.client.leave_room()

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Processes clicks on buttons."""
        for btn in self.buttons:
            btn.handle_click(x, y)

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Updates hover state on buttons."""
        for btn in self.buttons:
            btn.update_hover(x, y)

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
