from models.game_snapshot import GameSnapshot
from ui.interaction.mouse_handler import MouseHandler
from ui.rendering.renderer import Renderer
from ui.animation.animation_manager import AnimationManager
from ui.rendering.window import Window
from ui.ui_config import TIME_STEP_MS

class UIRunner:
    def __init__(self, controller, mouse_handler: MouseHandler, renderer: Renderer, 
                 animation_manager: AnimationManager, window: Window, time_step_ms: int = TIME_STEP_MS,
                 history_tracker = None):
        self.controller = controller
        self.mouse_handler = mouse_handler
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.window = window
        self.time_step_ms = time_step_ms
        self.history_tracker = history_tracker
        self.running = False

    def start_loop(self) -> None:
        """Main visual frame loop coordination."""
        self.running = True
        self.mouse_handler.register_callbacks()

        while self.running:
            snapshot = self.controller.get_snapshot()

            if self.history_tracker is not None:
                self.history_tracker.update(snapshot)

            self.animation_manager.sync_pieces(snapshot)

            self.animation_manager.update(self.time_step_ms / 1000.0, snapshot)

            canvas = self.renderer.render(snapshot, self.animation_manager.active_views)

            self.window.display(canvas, self.time_step_ms)

            self.controller.wait(self.time_step_ms)

            import cv2
            try:
                if cv2.getWindowProperty("Image", cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
            except Exception:
                pass
