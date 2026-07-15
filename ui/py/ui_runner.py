from models.game_snapshot import GameSnapshot
from ui.py.mouse_handler import MouseHandler
from ui.py.renderer import Renderer
from ui.py.animation_manager import AnimationManager
from ui.py.window import Window

class UIRunner:
    def __init__(self, controller, mouse_handler: MouseHandler, renderer: Renderer, 
                 animation_manager: AnimationManager, window: Window, time_step_ms: int = 50):
        self.controller = controller
        self.mouse_handler = mouse_handler
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.window = window
        self.time_step_ms = time_step_ms
        self.running = False

    def start_loop(self) -> None:
        """Main visual frame loop coordination."""
        self.running = True

        while self.running:
            self.mouse_handler.register_callbacks()

            snapshot = self.controller.get_snapshot()

            self.animation_manager.sync_pieces(snapshot)

            self.animation_manager.update(self.time_step_ms / 1000.0, snapshot)

            canvas = self.renderer.render(snapshot, self.animation_manager.active_views)

            self.window.display(canvas)

            self.controller.update(self.time_step_ms)

            import cv2
            try:
                if cv2.getWindowProperty("Image", cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
            except Exception:
                pass