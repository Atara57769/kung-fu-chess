import cv2
import time
import numpy as np
from typing import Optional
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen, ScreenType
from client.ui.components.button import Button
from client.ui.components.label import Label
from client.ui.ui_config import BG_COLOR_BGR

TITLE_MATCHMAKING = "MATCHMAKING"
STATUS_SEARCHING = "Searching for an opponent..."
LABEL_WAITING_TIME_FORMAT = "Waiting time: {}s"
BTN_LABEL_CANCEL = "Cancel"


class WaitingScreen(Screen):
    """Presents a loading/waiting state while searching for an opponent."""
    screen_type = ScreenType.WAITING
    
    def __init__(self, screen_manager, width: int, height: int) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        self.elapsed_time = 0.0
        self._start_time = time.time()
        
        self._setup_components()
 
    def _setup_components(self) -> None:
        """Initializes labels and cancel button on the waiting screen."""
        cx = self.width // 2
        
        self.labels.append(Label(cx, 120, TITLE_MATCHMAKING, centered=True))
        self.labels.append(Label(cx, 180, STATUS_SEARCHING, centered=True))
        self.labels.append(Label(cx, 220, LABEL_WAITING_TIME_FORMAT.format(0), centered=True))
        
        self.buttons.append(Button(cx - 100, 280, 200, 45, BTN_LABEL_CANCEL, self._on_cancel))
 
    def _on_cancel(self) -> None:
        """Cancels matchmaking and returns to the home screen."""
        from client.ui.screens.home_screen import HomeScreen
        home_screen = HomeScreen(self.screen_manager, self.width, self.height)
        self.screen_manager.switch_to(home_screen)
 
    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Handles click events on the cancel button."""
        for btn in self.buttons:
            btn.handle_click(x, y)
 
    def handle_mouse_move(self, x: int, y: int) -> None:
        """Updates hover states on button elements."""
        for btn in self.buttons:
            btn.update_hover(x, y)
 
    def update(self, dt: float) -> None:
        """Updates the elapsed time label using wall-clock time."""
        self.elapsed_time = time.time() - self._start_time
        self.labels[2].text = LABEL_WAITING_TIME_FORMAT.format(int(self.elapsed_time))
 
    def _draw_gradient_background(self, canvas: Img) -> None:
        """Fills canvas with a sleek dark radial-like vertical gradient."""
        c1 = np.array([25, 23, 21], dtype=np.float32)
        c2 = np.array([12, 10, 8], dtype=np.float32)
        
        for y in range(self.height):
            factor = y / self.height
            color = (1.0 - factor) * c1 + factor * c2
            canvas.img[y, :] = color.astype(np.uint8)
 
    def render(self, canvas: Img) -> None:
        """Renders the loading indicators, label text, and buttons."""
        if canvas.img is None:
            canvas.img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
        self._draw_gradient_background(canvas)
        
        for lbl in self.labels:
            lbl.render(canvas)
            
        for btn in self.buttons:
            btn.render(canvas)

