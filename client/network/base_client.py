"""
Abstract Base Class for Network Game Clients in Kung-Fu Chess.
Defines standard interface for both Monolithic (WS) and Distributed (REST + WS) client architectures.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from shared.models.cell import Cell


class BaseGameClient(ABC):
    """Abstract Base Class for Kung-Fu Chess game network clients."""

    @abstractmethod
    def start(self) -> None:
        """Starts background network handling loop."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops background network handling loop and closes active connections."""
        pass

    @abstractmethod
    def authenticate(self, username: str, password_or_token: str) -> None:
        """Authenticates user with server."""
        pass

    @abstractmethod
    def join_matchmaking(self) -> Any:
        """Joins matchmaking queue."""
        pass

    @abstractmethod
    def leave_matchmaking(self) -> Any:
        """Leaves matchmaking queue."""
        pass

    @abstractmethod
    def create_room(self, room_id: Optional[str] = None) -> None:
        """Creates a custom room."""
        pass

    @abstractmethod
    def join_room(self, room_id: str) -> None:
        """Joins an existing room."""
        pass

    @abstractmethod
    def leave_room(self) -> None:
        """Leaves the current room."""
        pass

    @abstractmethod
    def send_move(self, from_cell: Cell, to_cell: Cell) -> None:
        """Sends a piece move command."""
        pass

    @abstractmethod
    def send_jump(self, cell: Cell) -> None:
        """Sends a piece jump command."""
        pass
