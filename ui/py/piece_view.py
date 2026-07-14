from models.cell import Cell
from ui.py.board_geometry import BoardGeometry
from ui.py.animation.idle_state import IdleState
from ui.py.animation.move_state import MoveState
from ui.py.animation.jump_state import JumpState
from ui.py.animation.short_rest_state import ShortRestState
from ui.py.animation.long_rest_state import LongRestState
from models.game_snapshot import GameSnapshot

# Registry to instantiate states dynamically without branching
STATE_REGISTRY = {
    "idle": IdleState,
    "move": MoveState,
    "jump": JumpState,
    "short_rest": ShortRestState,
    "long_rest": LongRestState,
}

class PieceView:
    def __init__(self, color: str, kind: str, cell: Cell, geometry: BoardGeometry, asset_loader, snapshot: GameSnapshot):
        self.color = color.lower()
        self.kind = kind.upper()
        self.cell = cell
        self.geometry = geometry
        self.asset_loader = asset_loader
        
        # Current screen pixel coordinates (px, py)
        top_left = self.geometry.cell_to_top_left_pixel(self.cell)
        self.px = top_left[0]
        self.py = top_left[1]

        # Initial State is Idle
        self.state = None
        self.change_state("idle", snapshot)

    def change_state(self, state_name: str, snapshot: GameSnapshot) -> None:
        """Transitions this PieceView to a new animation state."""
        state_class = STATE_REGISTRY.get(state_name)
        if not state_class:
            raise ValueError(f"Unknown animation state: {state_name}")

        # Fetch cached assets (config dict and preloaded frames list) from AssetLoader
        assets = self.asset_loader.get_piece_assets(self.color, self.kind, state_name)
        
        old_state = self.state
        if old_state:
            old_state.on_exit(self, snapshot)

        self.state = state_class(
            name=state_name,
            config=assets["config"],
            sprites=assets["sprites"]
        )
        self.state.on_enter(self, snapshot)

    def update(self, dt: float, snapshot: GameSnapshot) -> None:
        """Updates active state logic and advances animation timers."""
        self.state.update(dt, self, snapshot)

    def get_sprite(self):
        """Returns the current frame Img of the piece."""
        return self.state.get_sprite()
