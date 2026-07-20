import logging
from typing import Dict, Any, Callable, Coroutine
from network.models import ConnectedPlayer

logger = logging.getLogger(__name__)

class PubSub:
    """Manages subscribing players to channels and publishing event notifications."""
    def __init__(self) -> None:
        # channel_id -> {player: callback}
        self._channels: Dict[str, Dict[ConnectedPlayer, Callable[[Any], Coroutine[Any, Any, None]]]] = {}

    def subscribe(self, channel: str, player: ConnectedPlayer, callback: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        """Subscribes a player's callback to a channel."""
        if channel not in self._channels:
            self._channels[channel] = {}
        self._channels[channel][player] = callback
        logger.debug(f"Subscribed {player.username or player.ip_address} to channel {channel}")

    def unsubscribe(self, channel: str, player: ConnectedPlayer) -> None:
        """Unsubscribes a player from a channel."""
        if channel in self._channels:
            if player in self._channels[channel]:
                del self._channels[channel][player]
                logger.debug(f"Unsubscribed {player.username or player.ip_address} from channel {channel}")
            if not self._channels[channel]:
                del self._channels[channel]

    async def publish(self, channel: str, message: Any) -> None:
        """Publishes a message to all subscribers of a channel."""
        if channel in self._channels:
            # Copy items to prevent dictionary modification during iteration
            for player, callback in list(self._channels[channel].items()):
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error executing callback for player {player.username or player.ip_address}: {e}")

def make_subscriber_callback(player: ConnectedPlayer, send_json_fn) -> Callable[[Any], Coroutine[Any, Any, None]]:
    """Creates a callback function that routes messages to the player's websocket connection."""
    async def callback(message: Any) -> None:
        await send_json_fn(player.ws, message)
    return callback
