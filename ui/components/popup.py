import cv2
from ui.rendering.img import Img
from ui.components.button import Button
from ui.ui_config import (
    POPUP_OVERLAY_COLOR, POPUP_BG_COLOR, POPUP_BORDER_COLOR,
    POPUP_TITLE_COLOR, POPUP_MSG_COLOR, POPUP_FONT_SCALE, POPUP_THICKNESS
)

class Popup:
    """A modal popup overlay component that intercepts inputs and blocks background actions."""
    
    def __init__(self, title: str, message: str, buttons_info: list[tuple[str, callable]]) -> None:
        self.title = title
        self.message = message
        self.visible = False
        
        # Dimensions of the popup box
        self.w = 400
        self.h = 220
        self.x = 0
        self.y = 0
        
        self.buttons: list[Button] = []
        self.buttons_info = buttons_info
        self.initialized_position = False

    def show(self, title: str = None, message: str = None) -> None:
        """Makes the popup visible with optional new title/message."""
        if title is not None:
            self.title = title
        if message is not None:
            self.message = message
        self.visible = True

    def hide(self) -> None:
        """Hides the popup and resets tracking flags."""
        self.visible = False

    def _initialize_layout(self, canvas_w: int, canvas_h: int) -> None:
        """Determines position and layouts buttons based on canvas dimensions."""
        self.x = (canvas_w - self.w) // 2
        self.y = (canvas_h - self.h) // 2
        
        self.buttons.clear()
        
        # Position buttons side-by-side or stacked
        n_buttons = len(self.buttons_info)
        if n_buttons > 0:
            btn_w = 120
            btn_h = 35
            spacing = 20
            total_btn_w = (btn_w * n_buttons) + (spacing * (n_buttons - 1))
            start_btn_x = self.x + (self.w - total_btn_w) // 2
            btn_y = self.y + self.h - 60
            
            for idx, (label, callback) in enumerate(self.buttons_info):
                bx = start_btn_x + idx * (btn_w + spacing)
                self.buttons.append(Button(bx, btn_y, btn_w, btn_h, label, callback))
                
        self.initialized_position = True

    def handle_click(self, mx: int, my: int) -> bool:
        """Processes clicks on popup buttons if visible. Intercepts all background clicks."""
        if not self.visible:
            return False
            
        # Check buttons first
        for btn in self.buttons:
            if btn.handle_click(mx, my):
                return True
                
        # Intercept anyway to block background actions
        return True

    def update_hover(self, mx: int, my: int) -> None:
        """Updates hover state of buttons if visible."""
        if not self.visible:
            return
        for btn in self.buttons:
            btn.update_hover(mx, my)

    def _draw_semi_transparent_overlay(self, canvas: Img) -> None:
        """Applies a dark semi-transparent tint over the whole application screen."""
        overlay = canvas.img.copy()
        h, w = canvas.img.shape[:2]
        cv2.rectangle(
            overlay, 
            (0, 0), 
            (w, h), 
            POPUP_OVERLAY_COLOR[:3], 
            thickness=-1
        )
        alpha = POPUP_OVERLAY_COLOR[3] / 255.0
        cv2.addWeighted(
            overlay, 
            alpha, 
            canvas.img, 
            1.0 - alpha, 
            0, 
            canvas.img
        )

    def _draw_popup_box(self, canvas: Img) -> None:
        """Draws the main popup window card."""
        cv2.rectangle(
            canvas.img, 
            (self.x, self.y), 
            (self.x + self.w, self.y + self.h), 
            POPUP_BG_COLOR, 
            thickness=-1
        )
        cv2.rectangle(
            canvas.img, 
            (self.x, self.y), 
            (self.x + self.w, self.y + self.h), 
            POPUP_BORDER_COLOR, 
            thickness=2
        )

    def _draw_text_labels(self, canvas: Img) -> None:
        """Draws title and message text onto the popup box."""
        # Render Title
        canvas.put_text(
            self.title, 
            self.x + 30, 
            self.y + 45, 
            POPUP_FONT_SCALE * 1.1, 
            POPUP_TITLE_COLOR, 
            POPUP_THICKNESS
        )
        
        # Render Message (basic multiline wrapped if contains newlines)
        lines = self.message.split('\n')
        current_y = self.y + 85
        for line in lines:
            canvas.put_text(
                line, 
                self.x + 30, 
                current_y, 
                POPUP_FONT_SCALE * 0.9, 
                POPUP_MSG_COLOR, 
                thickness=1
            )
            current_y += 24

    def render(self, canvas: Img) -> None:
        """Renders the entire modal popup if active."""
        if not self.visible or canvas.img is None:
            return
            
        h, w = canvas.img.shape[:2]
        if not self.initialized_position:
            self._initialize_layout(w, h)
            
        self._draw_semi_transparent_overlay(canvas)
        self._draw_popup_box(canvas)
        self._draw_text_labels(canvas)
        
        for btn in self.buttons:
            btn.render(canvas)
