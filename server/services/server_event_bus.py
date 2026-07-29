import logging
import weakref
from enum import Enum
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ServerEventType(Enum):
    ROOM_STATE_CHANGED = "room_state_changed"
    SNAPSHOT_UPDATED = "snapshot_updated"
    GAME_OVER = "game_over"
    MATCHMAKING_STATUS = "matchmaking_status"
    AUTH_RESPONSE = "auth_response"
    COUNTDOWN_TICK = "countdown_tick"
    ERROR_MESSAGE = "error_message"


@dataclass
class ServerEvent:
    event_type: ServerEventType
    target: Any = None  # ConnectedPlayer, GameRoom, WS, or List of ConnectedPlayer
    data: Any = None


class ServerEventBus:
    """Server-side publish-subscribe event bus for decoupled event routing."""

    def __init__(self) -> None:
        self._subscribers: Dict[ServerEventType, List[Any]] = {}

    def subscribe(self, event_type: ServerEventType, callback: Callable) -> None:
        """Subscribes a callback to a server event type using weak references when possible."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if hasattr(callback, "__self__") and callback.__self__ is not None:
            ref = weakref.WeakMethod(callback)
        else:
            ref = weakref.ref(callback)

        self._subscribers[event_type].append(ref)
        logger.debug(f"Subscribed callback to server event: {event_type.value}")

    def unsubscribe(self, event_type: ServerEventType, callback: Callable) -> None:
        """Unsubscribes a callback from a server event type."""
        if event_type not in self._subscribers:
            return

        new_list = []
        for ref in self._subscribers[event_type]:
            resolved = ref()
            if resolved is not None and resolved == callback:
                continue
            new_list.append(ref)
        self._subscribers[event_type] = new_list

    async def publish(self, event_type: ServerEventType, target: Any = None, data: Any = None) -> None:
        """Publishes an event to all subscribers asynchronously."""
        event = ServerEvent(event_type=event_type, target=target, data=data)
        if event_type not in self._subscribers:
            return

        active_refs = []
        for ref in self._subscribers[event_type]:
            callback = ref()
            if callback is not None:
                try:
                    res = callback(event)
                    if hasattr(res, "__await__"):
                        await res
                except Exception as e:
                    logger.error(f"Error executing callback for server event {event_type.value}: {e}", exc_info=True)
                active_refs.append(ref)
        self._subscribers[event_type] = active_refs
