import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional
from shared.constants import (
    ROOM_STATUS_ACTIVE, COLOR_NAME_WHITE, COLOR_NAME_BLACK, MSG_UNAUTHORIZED
)
from server.database.db_manager import DBManager
from shared.models.color import Color
from server.network.models import ConnectedPlayer, GameRoom
from server.services.game import game_session_service, disconnect_service
from server.services.auth import auth_service
from server.services.matchmaking import matchmaking_service, room_service
from shared.protocol import (
    MessageType, ErrorMessage, HeartbeatAckMessage, BaseMessage, parse_message
)

logger = logging.getLogger(__name__)

class GameCoordinator:
    """Coordinates authentication, matchmaking, and authoritative game state routing."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db = DBManager(db_path) if db_path else DBManager()
        self.rooms: Dict[str, GameRoom] = {}
        self.matchmaking_queue: List[ConnectedPlayer] = []
        self.send_json_fn = None
        self.message_handlers = {
            MessageType.MATCHMAKING: self._handle_matchmaking,
            MessageType.LEAVE_MATCHMAKING: self._handle_leave_matchmaking,
            MessageType.CREATE_ROOM: self._handle_create_room,
            MessageType.JOIN_ROOM: self._handle_join_room,
            MessageType.MOVE: self._handle_move,
            MessageType.JUMP: self._handle_jump,
            MessageType.LEAVE_ROOM: self._handle_leave_room,
            MessageType.GET_SNAPSHOT: self._handle_get_snapshot,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }

    def set_send_json_fn(self, send_json_fn) -> None:
        self.send_json_fn = send_json_fn

    async def dispatch_message(self, player: ConnectedPlayer, raw_msg: str) -> None:
        """Decodes JSON message and dispatches it to the correct action handler."""
        player.last_heartbeat = time.time()
        try:
            data = json.loads(raw_msg)
            msg = parse_message(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.warning("Received invalid or unparseable message.")
            return

        if msg.type == MessageType.AUTH:
            await auth_service.handle_auth(player, msg, self.db, self.send_json_fn)
        elif not player.authenticated:
            await self.send_json_fn(player.ws, ErrorMessage(message=MSG_UNAUTHORIZED))
        else:
            await self._handle_authenticated_message(player, msg)

    async def _handle_authenticated_message(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        """Dispatches authenticated client message command to its matching service using a dispatch map."""
        handler = self.message_handlers.get(msg.type)
        if handler:
            await handler(player, msg)
        else:
            logger.warning(f"Received unhandled message type: {msg.type}")

    async def _handle_matchmaking(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await matchmaking_service.add_to_matchmaking(player, self.matchmaking_queue, self.send_json_fn, self._start_matched_game)

    async def _handle_leave_matchmaking(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await matchmaking_service.remove_from_matchmaking(player, self.matchmaking_queue, self.send_json_fn)

    async def _handle_create_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        custom_id = getattr(msg, "room_id", None)
        await room_service.create_custom_room(player, self.rooms, self.send_json_fn, custom_id)

    async def _handle_join_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        room_id = getattr(msg, "room_id", "")
        await room_service.join_custom_room(player, room_id, self.rooms, self.send_json_fn, self.db)

    async def _handle_move(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        move_str = getattr(msg, "data", "")
        await game_session_service.process_game_move(player, move_str, self.rooms, self.send_json_fn)

    async def _handle_jump(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        cell_str = getattr(msg, "data", "")
        await game_session_service.process_game_jump(player, cell_str, self.rooms, self.send_json_fn)

    async def _handle_leave_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await room_service.handle_leave_room(player, self.rooms, self.send_json_fn)

    async def _handle_get_snapshot(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        room = self.rooms.get(player.room_id) if player.room_id else None
        if room:
            await game_session_service.send_snapshot_to(player, room, self.send_json_fn)

    async def _handle_heartbeat(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await self.send_json_fn(player.ws, HeartbeatAckMessage())

    async def _start_matched_game(self, p1: ConnectedPlayer, p2: ConnectedPlayer) -> None:
        """Pairs two matchmaking players into a new room and starts game."""
        room_id = str(random.randint(1000, 9999))
        while room_id in self.rooms:
            room_id = str(random.randint(1000, 9999))

        room = GameRoom(room_id)
        self.rooms[room_id] = room

        if random.choice([True, False]):
            room.white_player = p1
            room.black_player = p2
        else:
            room.white_player = p2
            room.black_player = p1

        room.white_player.room_id = room_id
        room.white_player.color = Color.WHITE
        room.black_player.room_id = room_id
        room.black_player.color = Color.BLACK

        logger.info(f"Matched Game started in Room {room_id}: White={room.white_player.username}, Black={room.black_player.username}")
        await game_session_service.start_game_session(room, self.db, self.send_json_fn)

    async def handle_disconnect(self, player: ConnectedPlayer) -> None:
        await disconnect_service.handle_disconnect(
            player, self.matchmaking_queue, self.rooms,
            lambda r: room_service.broadcast_room_state(r, self.send_json_fn),
            self.send_json_fn,
            lambda r, w: game_session_service.end_game(r, w, self.db, self.send_json_fn)
        )
