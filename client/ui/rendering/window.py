from client.ui.rendering.img import Img

class Window:
    def __init__(self, title: str = "Kung-Fu Chess"):
        self.title = title
        self.is_open = True

    def display(self, canvas: Img, delay: int) -> None:
        """Presents the canvas to the screen. All presentation must go through Img."""
        if not self.is_open:
            return
        
        canvas.refresh(delay)

    def close(self) -> None:
        """Closes the window representation."""
        self.is_open = False
        Img.close_window()
