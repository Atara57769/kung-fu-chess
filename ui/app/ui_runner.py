import cv2
from ui.rendering.img import Img
from ui.interaction.mouse_handler import MouseHandler
from ui.rendering.game_renderer import GameRenderer
from ui.animation.animation_manager import AnimationManager
from ui.rendering.window import Window
from ui.ui_config import TIME_STEP_MS
from ui.screens.screen_manager import ScreenManager
from ui.screens.game_screen import GameScreen

class UIRunner:
    def __init__(self, controller, mouse_handler: MouseHandler, renderer: GameRenderer, 
                 animation_manager: AnimationManager, window: Window, time_step_ms: int = TIME_STEP_MS,
                 history_tracker = None, screen_manager: ScreenManager = None):
        self.controller = controller
        self.mouse_handler = mouse_handler
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.window = window
        self.time_step_ms = time_step_ms
        self.history_tracker = history_tracker
        self.running = False
        
        if screen_manager is not None:
            self.screen_manager = screen_manager
        else:
            self.screen_manager = ScreenManager()
            geometry = mouse_handler.geometry if mouse_handler is not None else None
            game_screen = GameScreen(
                controller=self.controller,
                geometry=geometry,
                renderer=self.renderer,
                animation_manager=self.animation_manager,
                history_tracker=self.history_tracker
            )
            self.screen_manager.switch_to(game_screen)

    def _on_mouse_event(self, event: int, x: int, y: int, flags: int, param) -> None:
        """Translates mouse actions to the ScreenManager."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.screen_manager.handle_click(x, y, is_right=False)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.screen_manager.handle_click(x, y, is_right=True)
        elif event == cv2.EVENT_MOUSEMOVE:
            self.screen_manager.handle_mouse_move(x, y)


    def start_loop(self) -> None:
        """Main visual frame loop coordination."""
        self.running = True
        
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", self._on_mouse_event)

        while self.running:
            dt = self.time_step_ms / 1000.0
            
            self.screen_manager.update(dt)

            canvas = Img()
            self.screen_manager.render(canvas)

            self.window.display(canvas, self.time_step_ms)

            try:
                if cv2.getWindowProperty("Image", cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
            except Exception:
                pass

