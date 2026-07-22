import cv2
import numpy as np
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen
from client.ui.components.button import Button
from client.ui.components.label import Label
from client.ui.ui_config import BG_COLOR_BGR
from client.ui.screens.waiting_screen import WaitingScreen
from client.ui.components.room_dialog import RoomDialog
from client.ui.screens.room_screen import RoomScreen

DEFAULT_USERNAME = "Player"
TITLE_TEXT = "KUNG-FU CHESS"
WELCOME_TEXT_FORMAT = "Welcome, {} (ELO: {})"
BTN_LABEL_QUICK_MATCH = "Quick Match"
BTN_LABEL_CUSTOM_ROOM = "Custom Room"
ACTION_CREATE = "create"
ACTION_JOIN = "join"


class HomeScreen(Screen):
    """Presents the main home dashboard with matchmaking and room options."""
    
    def __init__(self, screen_manager, width: int, height: int, username: str = DEFAULT_USERNAME, rating: int = 1200, client=None) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        self.username = username
        self.rating = rating
        self.client = client
        
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        
        self._setup_components()
 
    def _setup_components(self) -> None:
        """Initializes the labels and buttons on the home screen."""
        cx = self.width // 2
        
        self.labels.append(Label(cx, 80, TITLE_TEXT, centered=True))
        self.labels.append(Label(cx, 130, WELCOME_TEXT_FORMAT.format(self.username, self.rating), centered=True))
        
        self.buttons.append(Button(cx - 130, 200, 260, 45, BTN_LABEL_QUICK_MATCH, self._on_quick_match))
        self.buttons.append(Button(cx - 130, 260, 260, 45, BTN_LABEL_CUSTOM_ROOM, self._on_custom_room_click))
 
    def _on_quick_match(self) -> None:
        """Triggers matchmaking and transitions to the waiting screen."""
        waiting_screen = WaitingScreen(self.screen_manager, self.width, self.height)
        self.screen_manager.switch_to(waiting_screen)
 
    def _on_custom_room_click(self) -> None:
        """Opens the native Tkinter room option popup modal."""
        dialog = RoomDialog()
        
        if dialog.result_action == ACTION_CREATE:
            if self.client:
                self.client.create_room(dialog.room_name if dialog.room_name else None)
        elif dialog.result_action == ACTION_JOIN:
            if dialog.room_name and self.client:
                self.client.join_room(dialog.room_name)
 
    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Directs mouse clicks to buttons."""
        for btn in self.buttons:
            btn.handle_click(x, y)
 
    def handle_mouse_move(self, x: int, y: int) -> None:
        """Directs cursor coordinates to components for hover effects."""
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
        """Renders the premium background, labels, and buttons."""
        if canvas.img is None:
            canvas.img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
        self._draw_gradient_background(canvas)
        
        for lbl in self.labels:
            lbl.render(canvas)
            
        for btn in self.buttons:
            btn.render(canvas)

