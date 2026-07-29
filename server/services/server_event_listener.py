import logging
from typing import Optional, Callable, Any
from server.network.models import ConnectedPlayer, GameRoom
from server.services.server_event_bus import ServerEventBus, ServerEventType, ServerEvent
from shared.protocol import (
    RoomStateMessage, SnapshotMessage, GameOverMessage,
    MatchmakingStatusMessage, AuthResponseMessage, CountdownMessage,
    ErrorMessage
)
from shared.protocol.protocol import serialize_snapshot
from shared.protocol.messages import BaseMessage

logger = logging.getLogger(__name__)


class ServerEventListener:
    """Server listener that subscribes to ServerEventBus state change events
    and sends appropriate network protocol messages to clients.
    """

    def __init__(self, event_bus: ServerEventBus, send: Optional[Callable] = None) -> None:
        self.event_bus = event_bus
        self.send = send
        self._subscribe_all()

    def set_send(self, send: Optional[Callable]) -> None:
        """Sets or updates the network send callable."""
        self.send = send

    def _subscribe_all(self) -> None:
        """Subscribes listener callbacks to all server event types."""
        self.event_bus.subscribe(ServerEventType.ROOM_STATE_CHANGED, self._on_room_state_changed)
        self.event_bus.subscribe(ServerEventType.SNAPSHOT_UPDATED, self._on_snapshot_updated)
        self.event_bus.subscribe(ServerEventType.GAME_OVER, self._on_game_over)
        self.event_bus.subscribe(ServerEventType.MATCHMAKING_STATUS, self._on_matchmaking_status)
        self.event_bus.subscribe(ServerEventType.AUTH_RESPONSE, self._on_auth_response)
        self.event_bus.subscribe(ServerEventType.COUNTDOWN_TICK, self._on_countdown_tick)
        self.event_bus.subscribe(ServerEventType.ERROR_MESSAGE, self._on_error_message)

    async def _send_to_client(self, client: Any, message: BaseMessage) -> None:
        """Helper to send a message to a client or ConnectedPlayer via send callback."""
        if not self.send:
            return
        ws = getattr(client, "ws", client)
        if ws is not None:
            await self.send(ws, message)

    async def _on_room_state_changed(self, event: ServerEvent) -> None:
        """Handles room state changes and broadcasts roster to participants."""
        if not self.send:
            return

        if isinstance(event.target, ConnectedPlayer) and isinstance(event.data, RoomStateMessage):
            await self._send_to_client(event.target, event.data)
            return

        if not isinstance(event.target, GameRoom):
            return

        room = event.target
        if not room:
            return

        white_name = room.white_player.username if room.white_player else None
        black_name = room.black_player.username if room.black_player else None
        specs = [p.username for p in room.spectators if p.username]

        clients = []
        if room.white_player:
            clients.append(room.white_player)
        if room.black_player:
            clients.append(room.black_player)
        clients.extend(room.spectators)

        for c in clients:
            msg = RoomStateMessage(
                room_id=room.room_id,
                white=white_name,
                black=black_name,
                spectators=specs,
                status=room.status,
                your_color=c.color.value if c.color else None
            )
            await self._send_to_client(c, msg)

    async def _on_snapshot_updated(self, event: ServerEvent) -> None:
        """Handles snapshot updates for a room or single player."""
        if not self.send:
            return

        if isinstance(event.data, SnapshotMessage) and event.target:
            await self._send_to_client(event.target, event.data)
            return

        room = event.target
        if not room:
            return

        player = event.data.get("player") if isinstance(event.data, dict) else None
        if player:
            snap = room.controller.get_snapshot(player_color=player.color)
            await self._send_to_client(player, SnapshotMessage(data=serialize_snapshot(snap)))
            return

        clients = []
        if room.white_player:
            clients.append(room.white_player)
        if room.black_player:
            clients.append(room.black_player)
        clients.extend(room.spectators)

        for c in clients:
            snap = room.controller.get_snapshot(player_color=c.color)
            await self._send_to_client(c, SnapshotMessage(data=serialize_snapshot(snap)))

    async def _on_game_over(self, event: ServerEvent) -> None:
        """Handles game over event and sends GameOverMessage to participants."""
        if not self.send:
            return

        room = event.target
        payload = event.data  

        if not room or not payload:
            return

        clients = []
        if room.white_player:
            clients.append(room.white_player)
        if room.black_player:
            clients.append(room.black_player)
        clients.extend(room.spectators)

        for c in clients:
            await self._send_to_client(c, payload)

    async def _on_matchmaking_status(self, event: ServerEvent) -> None:
        """Handles matchmaking status changes."""
        if not self.send or not event.target:
            return
        msg = event.data if isinstance(event.data, MatchmakingStatusMessage) else MatchmakingStatusMessage(status=str(event.data))
        await self._send_to_client(event.target, msg)

    async def _on_auth_response(self, event: ServerEvent) -> None:
        """Handles authentication response events."""
        if not self.send or not event.target:
            return
        msg = event.data if isinstance(event.data, AuthResponseMessage) else event.data
        if isinstance(msg, BaseMessage):
            await self._send_to_client(event.target, msg)

    async def _on_countdown_tick(self, event: ServerEvent) -> None:
        """Handles disconnect auto-resign countdown ticks."""
        if not self.send or not event.target:
            return
        msg = event.data if isinstance(event.data, CountdownMessage) else event.data
        if isinstance(msg, BaseMessage):
            await self._send_to_client(event.target, msg)

    async def _on_error_message(self, event: ServerEvent) -> None:
        """Handles error messages to a client."""
        if not self.send or not event.target:
            return
        msg = event.data if isinstance(event.data, ErrorMessage) else ErrorMessage(message=str(event.data))
        await self._send_to_client(event.target, msg)
