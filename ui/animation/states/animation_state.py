from abc import ABC, abstractmethod
from ui.rendering.img import Img
from models.game_snapshot import GameSnapshot
from ui.animation.state_types import AnimationStateId

class AnimationState(ABC):
    def __init__(self, name: str, config: dict, sprites: list[Img]):
        self.name = name
        self.config = config
        self.sprites = sprites
        self.elapsed_time = 0.0
        self.current_frame_index = 0

    def on_enter(self, piece_view, snapshot: GameSnapshot) -> None:
        """Called when entering the state. Reset time and frame index."""
        self.elapsed_time = 0.0
        self.current_frame_index = 0
        if hasattr(piece_view, "target_cell"):
            delattr(piece_view, "target_cell")

    def on_exit(self, piece_view, snapshot: GameSnapshot) -> None:
        """Called when exiting the state."""
        pass

    @abstractmethod
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        """
        Advances elapsed time, updates frame index, handles visual coordinate
        interpolation, and checks for transitions.
        """
        pass

    def get_sprite(self) -> Img:
        """Returns the current sprite Img corresponding to the frame index."""
        if not self.sprites:
            raise ValueError(f"No sprites loaded for state {self.name}")
        return self.sprites[self.current_frame_index]

    def advance_frames(self, dt: float) -> None:
        """Helper to advance the current frame index based on frame rate and loop config."""
        if not self.sprites:
            return

        fps = self.config.get("graphics", {}).get("frames_per_sec", 10)
        is_loop = self.config.get("graphics", {}).get("is_loop", True)

        self.elapsed_time += dt
        frame_duration = 1.0 / fps if fps > 0 else 0.1
        
        total_frames = len(self.sprites)
        raw_frame_index = int(self.elapsed_time / frame_duration)

        if is_loop:
            self.current_frame_index = raw_frame_index % total_frames
        else:
            self.current_frame_index = min(raw_frame_index, total_frames - 1)
