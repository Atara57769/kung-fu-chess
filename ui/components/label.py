import cv2
from ui.rendering.img import Img
from ui.ui_config import LBL_TEXT_COLOR, LBL_FONT_SCALE, LBL_THICKNESS

class Label:
    """A standard static text Label component rendering on an Img canvas."""
    
    def __init__(self, x: int, y: int, text: str, centered: bool = False) -> None:
        self.x = x
        self.y = y
        self.text = text
        self.centered = centered
        
        self.color = LBL_TEXT_COLOR
        self.font_scale = LBL_FONT_SCALE
        self.thickness = LBL_THICKNESS

    def _get_draw_position(self) -> tuple[int, int]:
        """Calculates coordinates of text start, handling centering if enabled."""
        if not self.centered:
            return self.x, self.y
            
        (tw, th), baseline = cv2.getTextSize(
            self.text, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            self.font_scale, 
            self.thickness
        )
        # Center horizontally, keep baseline at vertical y
        return self.x - tw // 2, self.y

    def render(self, canvas: Img) -> None:
        """Renders the text label to the canvas."""
        if canvas.img is None:
            return
        draw_x, draw_y = self._get_draw_position()
        canvas.put_text(
            self.text, 
            draw_x, 
            draw_y, 
            self.font_scale, 
            self.color, 
            self.thickness
        )
