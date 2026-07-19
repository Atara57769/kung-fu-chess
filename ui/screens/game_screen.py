from ui.screens.base_screen import Screen
from ui.rendering.img import Img

class GameScreen(Screen):
    """Integrates the active game engine and controller into the screen architecture."""
    
    def __init__(self, controller, geometry, renderer, animation_manager, history_tracker=None) -> None:
        self.controller = controller
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.history_tracker = history_tracker

    def _get_cell_from_coordinates(self, x: int, y: int) -> any:
        """Translates pixel coordinates to board cell taking left padding into account."""
        board_x = x - self.renderer.left_padding
        return self.geometry.pixel_to_cell(board_x, y)

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Translates coordinates and dispatches click or jump to controller."""
        cell = self._get_cell_from_coordinates(x, y)
        if is_right:
            self.controller.jump(cell)
        else:
            self.controller.click(cell)

    def update(self, dt: float) -> None:
        """Advances animations and ticks the controller."""
        snapshot = self.controller.get_snapshot()
        
        if self.history_tracker is not None:
            self.history_tracker.update(snapshot)
            
        self.animation_manager.sync_pieces(snapshot)
        self.animation_manager.update(dt, snapshot)
        
        # Advance the local controller's game engine clocks
        self.controller.wait(int(dt * 1000))

    def render(self, canvas: Img) -> None:
        """Renders the game board, pieces, overlays and history panels onto canvas."""
        snapshot = self.controller.get_snapshot()
        rendered_canvas = self.renderer.render(snapshot, self.animation_manager.active_views)
        canvas.img = rendered_canvas.img
