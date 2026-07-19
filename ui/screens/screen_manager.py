from ui.rendering.img import Img
from ui.screens.base_screen import Screen

class ScreenManager:
    """Controls the active screen state and delegates events."""
    
    def __init__(self) -> None:
        self.active_screen: Screen | None = None

    def switch_to(self, screen: Screen) -> None:
        """Transitions the application to a new screen state."""
        self.active_screen = screen

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Delegates mouse click event to the active screen."""
        if self.active_screen is not None:
            self.active_screen.handle_click(x, y, is_right)

    def update(self, dt: float) -> None:
        """Delegates tick update to the active screen."""
        if self.active_screen is not None:
            self.active_screen.update(dt)

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Delegates mouse movement/hover event to the active screen."""
        if self.active_screen is not None and hasattr(self.active_screen, "handle_mouse_move"):
            self.active_screen.handle_mouse_move(x, y)

    def render(self, canvas: Img) -> None:
        """Delegates rendering to the active screen."""
        if self.active_screen is not None:
            self.active_screen.render(canvas)

