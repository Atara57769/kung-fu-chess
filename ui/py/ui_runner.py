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
            # 1. Re-register mouse handlers to the active OpenCV window structure
            self.mouse_handler.register_callbacks()

            # 2. Get current game state snapshot
            snapshot = self.controller.get_snapshot()

            # 3. Synchronize active visual PieceViews
            self.animation_manager.sync_pieces(snapshot)

            # 4. Update animations with logical delta time (converted to seconds)
            self.animation_manager.update(self.time_step_ms / 1000.0, snapshot)

            # 5. Render composite frame
            canvas = self.renderer.render(snapshot, self.animation_manager.active_views)

            # 6. Display the canvas (blocks on Img.show() waitKey until key press)
            self.window.display(canvas)

            # 7. Advance the game logic clock
            self.controller.update(self.time_step_ms)

            # Check if the window was closed by the user
            import cv2
            try:
                if cv2.getWindowProperty("Image", cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
            except Exception:
                pass

            # Check if game over condition is hit
            if snapshot.game_over:
                self.running = False
