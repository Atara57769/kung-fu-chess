from client.ui.rendering.img import Img

class Screen:
    """Base interface for all UI screen states."""
    
    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Called when a mouse click event occurs at coordinates (x, y)."""
        pass

    def update(self, dt: float) -> None:
        """Called to update the screen state every tick/frame."""
        pass

    def render(self, canvas: Img) -> None:
        """Called to draw the screen components onto the canvas Img."""
        pass
