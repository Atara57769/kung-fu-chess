import logging
import weakref
from typing import Callable, Any, Dict, List

logger = logging.getLogger(__name__)

class ClientPubSub:
    """A thread-safe and memory-safe client-side publish-subscribe event hub."""
    
    def __init__(self) -> None:
        # Mapping of event_type -> list of weak references to callbacks
        self._subscribers: Dict[str, List[Any]] = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribes a callback to an event type using weak references to prevent leaks."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
            
        if hasattr(callback, "__self__") and callback.__self__ is not None:
            ref = weakref.WeakMethod(callback)
        else:
            ref = weakref.ref(callback)
            
        self._subscribers[event_type].append(ref)
        logger.debug(f"Subscribed callback to local event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Manually unsubscribes a callback from an event type."""
        if event_type not in self._subscribers:
            return
            
        new_list = []
        for ref in self._subscribers[event_type]:
            resolved = ref()
            if resolved is not None and resolved == callback:
                continue
            new_list.append(ref)
        self._subscribers[event_type] = new_list
        logger.debug(f"Unsubscribed callback from local event: {event_type}")

    def publish(self, event_type: str, *args, **kwargs) -> None:
        """Publishes an event to all active subscribers, cleaning up dead references."""
        if event_type not in self._subscribers:
            return
            
        active_refs = []
        for ref in self._subscribers[event_type]:
            callback = ref()
            if callback is not None:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error executing local callback for event {event_type}: {e}", exc_info=True)
                active_refs.append(ref)
                
        self._subscribers[event_type] = active_refs
