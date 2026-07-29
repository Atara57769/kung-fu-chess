from abc import ABC, abstractmethod
from enum import Enum, auto
from client.ui.rendering.img import Img

class ScreenType(Enum):
    BASE = auto()
    HOME = auto()
    WAITING = auto()
    ROOM = auto()
    ONLINE_GAME = auto()

class Screen(ABC):
    """Base interface for all UI screen states."""
    screen_type: ScreenType = ScreenType.BASE

    @abstractmethod
    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Called when a mouse click event occurs at coordinates (x, y)."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Called to update the screen state every tick/frame."""
        pass

    @abstractmethod
    def render(self, canvas: Img) -> None:
        """Called to draw the screen components onto the canvas Img."""
        pass

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Called when a mouse move event occurs at coordinates (x, y). Defaults to no-op."""
        pass

