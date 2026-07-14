import cv2
from ui.py.board_geometry import BoardGeometry

class MouseHandler:
    def __init__(self, controller, geometry: BoardGeometry):
        self.controller = controller
        self.geometry = geometry

    def register_callbacks(self) -> None:
        """
        Creates or binds to the named window "Image" (which is used by Img.show())
        and sets the mouse callback to intercept clicks.
        """
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", self.on_mouse_event)

    def on_mouse_event(self, event: int, x: int, y: int, flags: int, param) -> None:
        """Callback to handle OpenCV mouse events."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Left Click: Select / Move
            self.controller.click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Right Click: Jump
            self.controller.jump(x, y)
