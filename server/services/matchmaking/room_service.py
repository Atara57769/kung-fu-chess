import logging
import uuid
from enum import Enum
from typing import Dict, Optional, Tuple, Callable
from server.network.models import ConnectedPlayer, GameRoom
from shared.protocol import ErrorMessage, RoomStateMessage
from shared.models.color import Color
from shared.constants import (
    ROOM_STATUS_WAITING, ROOM_STATUS_ACTIVE,
    MSG_ROOM_ALREADY_EXISTS, MSG_ROOM_NOT_FOUND
)

logger = logging.getLogger(__name__)


class RoomJoinEvent(Enum):
    NOT_FOUND = "not_found"
    RECONNECTED = "reconnected"
    GAME_CAN_START = "game_can_start"
    SPECTATOR_ACTIVE = "spectator_active"
    SPECTATOR_WAITING = "spectator_waiting"


class RoomService:
    """Manages room membership: creating, joining, leaving, and broadcasting room state.
    Has no knowledge of game session logic — returns events for the coordinator to act on.
    """

    def __init__(self, send: Optional[Callable] = None) -> None:
        self.send = send


    def build_room(self, room_id: str, rooms: Dict[str, GameRoom],
                   white: ConnectedPlayer, black: Optional[ConnectedPlayer] = None) -> GameRoom:
        """Single room factory: assigns white (and optionally black) with colors and room_id."""
        room = GameRoom(room_id)
        room.white_player = white
        white.room_id = room_id
        white.color = Color.WHITE
        if black is not None:
            room.black_player = black
            black.room_id = room_id
            black.color = Color.BLACK
        rooms[room_id] = room
        return room

    async def create_room(self, player: ConnectedPlayer, rooms: Dict[str, GameRoom], room_id: Optional[str] = None) -> None:
        """Creates a custom lobby, seats the creator as White, and broadcasts state."""
        if not room_id:
            room_id = uuid.uuid4().hex[:8]
        elif room_id in rooms:
            if self.send:
                await self.send(player.ws, ErrorMessage(message=MSG_ROOM_ALREADY_EXISTS))
            return

        room = self.build_room(room_id, rooms, white=player)
        logger.info(f"Custom Room {room_id} created by {player.username}.")
        await self.broadcast_room_state(room)


    async def join_room(self, player: ConnectedPlayer, room_id: str, rooms: Dict[str, GameRoom]) -> Tuple[RoomJoinEvent, Optional[GameRoom]]:
        """Joins a lobby. Returns (RoomJoinEvent, room) so the coordinator decides game-level actions."""
        room = rooms.get(room_id)
        if not room:
            if self.send:
                await self.send(player.ws, ErrorMessage(message=MSG_ROOM_NOT_FOUND))
            return RoomJoinEvent.NOT_FOUND, None

        player.room_id = room_id

        if room.white_player and room.white_player.username == player.username and room.white_player != player:
            return await self._reconnect_player(room, player, Color.WHITE)

        if room.black_player and room.black_player.username == player.username and room.black_player != player:
            return await self._reconnect_player(room, player, Color.BLACK)

        if room.black_player is None and room.status == ROOM_STATUS_WAITING:
            room.black_player = player
            player.color = Color.BLACK
            logger.info(f"Player {player.username} joined Room {room_id} as Black.")
            return RoomJoinEvent.GAME_CAN_START, room

        room.spectators.append(player)
        player.color = None
        logger.info(f"Player {player.username} joined Room {room_id} as Spectator.")
        await self.broadcast_room_state(room)
        if room.status == ROOM_STATUS_ACTIVE:
            return RoomJoinEvent.SPECTATOR_ACTIVE, room
        return RoomJoinEvent.SPECTATOR_WAITING, room

    async def _reconnect_player(self, room: GameRoom, player: ConnectedPlayer, color: Color) -> tuple["RoomJoinEvent", GameRoom]:
        """Seats a reconnecting player back into their slot and cancels any pending countdown."""
        if color == Color.WHITE:
            room.white_player = player
        else:
            room.black_player = player
        player.color = color
        if room.countdown_task:
            room.countdown_task.cancel()
            room.countdown_task = None
        logger.info(f"Player {player.username} reconnected to Room {room.room_id} as {color.name.capitalize()}.")
        await self.broadcast_room_state(room)
        return RoomJoinEvent.RECONNECTED, room

    async def leave_room(self, player: ConnectedPlayer, rooms: Dict[str, GameRoom]) -> None:
        """Removes a player from their current lobby session."""
        if not player.room_id:
            return
        room_id = player.room_id
        room = rooms.get(room_id)
        if not room:
            return

        if room.white_player == player:
            room.white_player = None
        elif room.black_player == player:
            room.black_player = None
        elif player in room.spectators:
            room.spectators.remove(player)

        player.room_id = None
        player.color = None
        await self.broadcast_room_state(room)
        if self.send:
            await self.send(player.ws, RoomStateMessage(room_id=None))

    async def broadcast_room_state(self, room: GameRoom) -> None:
        """Sends current lobby roster to all participants."""
        if not self.send:
            return
        white_name = room.white_player.username if room.white_player else None
        black_name = room.black_player.username if room.black_player else None
        specs = [p.username for p in room.spectators if p.username]

        clients = []
        if room.white_player: clients.append(room.white_player)
        if room.black_player: clients.append(room.black_player)
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
            await self.send(c.ws, msg)
