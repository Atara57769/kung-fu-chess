import cv2
from ui.board.board_geometry import BoardGeometry

class MouseHandler:
    def __init__(self, controller, geometry: BoardGeometry, left_padding: int = 0):
        self.controller = controller
        self.geometry = geometry
        self.left_padding = left_padding

    def register_callbacks(self) -> None:
        """
        Creates or binds to the named window "Image" (which is used by Img.show())
        and sets the mouse callback to intercept clicks.
        """
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", self.on_mouse_event)

    def on_mouse_event(self, event: int, x: int, y: int, flags: int, param) -> None:
        """Callback to handle OpenCV mouse events."""
        board_x = x - self.left_padding
        cell = self.geometry.pixel_to_cell(board_x, y)

        if event == cv2.EVENT_LBUTTONDOWN:
            self.controller.click(cell)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.controller.jump(cell)
