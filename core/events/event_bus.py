from typing import Dict, List, Callable, Type, Any

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[Type[Any], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[Any], callback: Callable[[Any], None]) -> None:
        """
        Register a callback for an event type.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: Type[Any], callback: Callable[[Any], None]) -> None:
        """
        Remove a previously registered callback.
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def publish(self, event: Any) -> None:
        """
        Invoke every callback registered for type(event).
        """
        event_type = type(event)
        callbacks = self._subscribers.get(event_type)
        if callbacks:
            # Create a copy of callbacks list in case callbacks unsubscribe themselves during iteration
            for callback in list(callbacks):
                callback(event)
