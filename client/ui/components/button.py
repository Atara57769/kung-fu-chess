import cv2
from client.ui.rendering.img import Img
from client.ui.ui_config import (
    BTN_BG_COLOR, BTN_HOVER_BG_COLOR, BTN_BORDER_COLOR, 
    BTN_TEXT_COLOR, BTN_FONT_SCALE, BTN_THICKNESS
)

class Button:
    """A standard interactive UI Button component rendering on an Img canvas."""
    
    def __init__(self, x: int, y: int, w: int, h: int, text: str, callback: callable) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.callback = callback
        
        self.bg_color = BTN_BG_COLOR
        self.hover_bg_color = BTN_HOVER_BG_COLOR
        self.border_color = BTN_BORDER_COLOR
        self.text_color = BTN_TEXT_COLOR
        self.font_scale = BTN_FONT_SCALE
        self.thickness = BTN_THICKNESS
        self.is_hovered = False

    def is_point_inside(self, px: int, py: int) -> bool:
        """Returns True if pixel coordinates (px, py) lie within the button rectangle."""
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def update_hover(self, mx: int, my: int) -> None:
        """Updates the button hover state based on cursor coordinates."""
        self.is_hovered = self.is_point_inside(mx, my)

    def handle_click(self, mx: int, my: int) -> bool:
        """Invokes the callback if clicked, returning success status."""
        if self.is_point_inside(mx, my):
            self.callback()
            return True
        return False

    def _draw_background(self, canvas: Img) -> None:
        """Draws the filled background of the button."""
        color = self.hover_bg_color if self.is_hovered else self.bg_color
        cv2.rectangle(
            canvas.img, 
            (self.x, self.y), 
            (self.x + self.w, self.y + self.h), 
            color, 
            thickness=-1
        )

    def _draw_border(self, canvas: Img) -> None:
        """Draws the border outline of the button."""
        cv2.rectangle(
            canvas.img, 
            (self.x, self.y), 
            (self.x + self.w, self.y + self.h), 
            self.border_color, 
            thickness=1
        )

    def _draw_text(self, canvas: Img) -> None:
        """Centers and draws the button label text."""
        (tw, th), baseline = cv2.getTextSize(
            self.text, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            self.font_scale, 
            self.thickness
        )
        tx = self.x + (self.w - tw) // 2
        ty = self.y + (self.h + th) // 2
        canvas.put_text(
            self.text, 
            tx, 
            ty, 
            self.font_scale, 
            self.text_color, 
            self.thickness
        )

    def render(self, canvas: Img) -> None:
        """Renders the button component to the canvas."""
        if canvas.img is None:
            return
        self._draw_background(canvas)
        self._draw_border(canvas)
        self._draw_text(canvas)
