import cv2
import numpy as np
from client.ui.rendering.img import Img
from client.ui.screens.base_screen import Screen
from client.ui.components.button import Button
from client.ui.components.label import Label
from client.ui.ui_config import BG_COLOR_BGR

class WaitingScreen(Screen):
    """Presents a loading/waiting state while searching for an opponent."""
    
    def __init__(self, screen_manager, width: int, height: int) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        
        self._setup_components()

    def _setup_components(self) -> None:
        """Initializes labels and cancel button on the waiting screen."""
        cx = self.width // 2
        
        self.labels.append(Label(cx, 120, "MATCHMAKING", centered=True))
        self.labels.append(Label(cx, 180, "Searching for an opponent...", centered=True))
        self.labels.append(Label(cx, 220, "Waiting time: 0s", centered=True))
        
        self.buttons.append(Button(cx - 100, 280, 200, 45, "Cancel", self._on_cancel))
        self.elapsed_time = 0.0

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
        """Ticks the elapsed matchmaking time and updates the duration label."""
        self.elapsed_time += dt
        # Update the time label text
        self.labels[2].text = f"Waiting time: {int(self.elapsed_time)}s"

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
