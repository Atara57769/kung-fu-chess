import cv2
import logging
from client.ui.rendering.img import Img
from client.ui.rendering.window import Window
from client.ui.screens.screen_manager import ScreenManager
from client.ui.ui_config import TIME_STEP_MS
from client.ui.app.online_coordinator import OnlineCoordinator

WINDOW_NAME_IMAGE = "Image"

class OnlineUIRunner:
    def __init__(self, client, screen_manager: ScreenManager, window: Window,
                 coordinator: OnlineCoordinator, time_step_ms: int = TIME_STEP_MS) -> None:
        self.client = client
        self.screen_manager = screen_manager
        self.window = window
        self.coordinator = coordinator
        self.time_step_ms = time_step_ms
        self.running = False
        self.logger = logging.getLogger(__name__)

    def _on_mouse_event(self, event: int, x: int, y: int, flags: int, param) -> None:
        """Translates mouse actions to the ScreenManager."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.screen_manager.handle_click(x, y, is_right=False)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.screen_manager.handle_click(x, y, is_right=True)
        elif event == cv2.EVENT_MOUSEMOVE:
            self.screen_manager.handle_mouse_move(x, y)

    def start_loop(self) -> None:
        """Main online visual frame loop coordination."""
        self.running = True
        
        cv2.namedWindow(WINDOW_NAME_IMAGE)
        cv2.setMouseCallback(WINDOW_NAME_IMAGE, self._on_mouse_event)
        
        self.logger.info("Starting online visual frame loop...")
        while self.running:
            dt = self.time_step_ms / 1000.0
            
            self.coordinator.update(dt)
            
            self.screen_manager.update(dt)
            
            canvas = Img()
            self.screen_manager.render(canvas)
            self.window.display(canvas, self.time_step_ms)
            
            try:
                if cv2.getWindowProperty(WINDOW_NAME_IMAGE, cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
            except Exception:
                pass

