from img import Img

class Window:
    def __init__(self, title: str = "Kung-Fu Chess"):
        self.title = title
        self.is_open = True

    def display(self, canvas: Img) -> None:
        """Presents the canvas to the screen. All presentation must go through Img."""
        if not self.is_open:
            return
        
        # Display the canvas using the existing show method of Img
        canvas.show()

    def close(self) -> None:
        """Closes the window representation."""
        self.is_open = False
