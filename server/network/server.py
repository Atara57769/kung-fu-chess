import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional
import websockets
from websockets.exceptions import ConnectionClosed
from shared.constants import (
    DEFAULT_HOST, DEFAULT_PORT, HEARTBEAT_TIMEOUT, DISCONNECT_COUNTDOWN, DEFAULT_BOARD_LAYOUT,
    FIELD_TYPE, FIELD_MESSAGE, FIELD_ROOM_ID, FIELD_DATA,
    ROOM_STATUS_ACTIVE, COLOR_NAME_WHITE, COLOR_NAME_BLACK, GAME_RESULT_DRAW,
    MSG_UNAUTHORIZED
)
from server.database.db_manager import DBManager
from shared.models.color import Color
from server.network.models import ConnectedPlayer, GameRoom
from server.services.game import game_session_service, disconnect_service
from server.services.auth import auth_service
from server.services.matchmaking import matchmaking_service, room_service
from shared.protocol import MessageType

logger = logging.getLogger(__name__)


class GameServer:
    """WebSocket server coordinating authentication, matchmaking, and authoritative game state."""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str = None) -> None:
        self.host = host
        self.port = port
        self.db = DBManager(db_path) if db_path else DBManager()
        self.players: Dict[any, ConnectedPlayer] = {}
        self.rooms: Dict[str, GameRoom] = {}
        self.matchmaking_queue: List[ConnectedPlayer] = []
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

    async def start(self) -> None:
        """Starts the WebSocket server listening loop."""
        async def _internal_handler(ws, path=None):
            await self.handle_client_connection(ws)
            
        async with websockets.serve(_internal_handler, self.host, self.port):
            logger.info(f"Kung-Fu Chess Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()

    async def handle_client_connection(self, websocket) -> None:
        """Entry handler for each new WebSocket connection client."""
        ip = websocket.remote_address[0]
        player = ConnectedPlayer(websocket, ip)
        self.players[websocket] = player
        logger.info(f"Connection opened from {ip}")
        
        try:
            async for message in websocket:
                await self.dispatch_message(player, message)
        except ConnectionClosed:
            logger.info(f"Connection closed by client {ip}")
        finally:
            await self.handle_disconnect(player)
            if websocket in self.players:
                del self.players[websocket]

    async def dispatch_message(self, player: ConnectedPlayer, raw_msg: str) -> None:
        """Decodes JSON message and dispatches it to the correct action handler."""
        player.last_heartbeat = time.time()
        try:
            data = json.loads(raw_msg)
        except json.JSONDecodeError:
            logger.warning("Received invalid non-JSON message.")
            return

        msg_type = data.get(FIELD_TYPE)
        if msg_type == MessageType.AUTH:
            await auth_service.handle_auth(player, data, self.db, self._send_json)
        elif not player.authenticated:
            await self._send_json(player.ws, {FIELD_TYPE: MessageType.ERROR, FIELD_MESSAGE: MSG_UNAUTHORIZED})
        else:
            await self._handle_authenticated_message(player, msg_type, data)

    async def _handle_authenticated_message(self, player: ConnectedPlayer, msg_type: str, data: dict) -> None:
        """Dispatches authenticated client message command to its matching service using a dispatch map."""
        handler = self.message_handlers.get(msg_type)
        if handler:
            await handler(player, data)
        else:
            logger.warning(f"Received unhandled message type: {msg_type}")

    async def _handle_matchmaking(self, player: ConnectedPlayer, data: dict) -> None:
        await matchmaking_service.add_to_matchmaking(player, self.matchmaking_queue, self._send_json, self._start_matched_game)

    async def _handle_leave_matchmaking(self, player: ConnectedPlayer, data: dict) -> None:
        await matchmaking_service.remove_from_matchmaking(player, self.matchmaking_queue, self._send_json)

    async def _handle_create_room(self, player: ConnectedPlayer, data: dict) -> None:
        custom_id = data.get(FIELD_ROOM_ID)
        await room_service.create_custom_room(player, self.rooms, self._send_json, self.broadcast_room_state, custom_id)

    async def _handle_join_room(self, player: ConnectedPlayer, data: dict) -> None:
        await room_service.join_custom_room(
            player, data.get(FIELD_ROOM_ID, ""), self.rooms, self._send_json,
            self.broadcast_room_state, self._start_game_session, self.send_snapshot_to
        )

    async def _handle_move(self, player: ConnectedPlayer, data: dict) -> None:
        await game_session_service.process_game_move(player, data.get(FIELD_DATA, ""), self.rooms, self.broadcast_snapshot)


    async def _handle_jump(self, player: ConnectedPlayer, data: dict) -> None:
        await game_session_service.process_game_jump(player, data.get(FIELD_DATA, ""), self.rooms, self.broadcast_snapshot)

    async def _handle_leave_room(self, player: ConnectedPlayer, data: dict) -> None:
        await room_service.handle_leave_room(player, self.rooms, self._send_json, self.broadcast_room_state)

    async def _handle_get_snapshot(self, player: ConnectedPlayer, data: dict) -> None:
        room = self.rooms.get(player.room_id) if player.room_id else None
        if room:
            await self.send_snapshot_to(player, room)

    async def _handle_heartbeat(self, player: ConnectedPlayer, data: dict) -> None:
        await self._send_json(player.ws, {FIELD_TYPE: MessageType.HEARTBEAT_ACK})

    async def _send_json(self, ws, data: dict) -> None:
        """Utility to safely send a JSON string to a WebSocket client."""
        try:
            await ws.send(json.dumps(data))
        except ConnectionClosed:
            pass

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
        await self._start_game_session(room)

    async def _start_game_session(self, room: GameRoom) -> None:
        await game_session_service.start_game_session(room, self.broadcast_room_state, self.broadcast_snapshot, self.db, self._send_json)

    async def broadcast_room_state(self, room: GameRoom) -> None:
        await room_service.broadcast_room_state(room, self._send_json)

    async def broadcast_snapshot(self, room: GameRoom) -> None:
        await game_session_service.broadcast_snapshot(room, self._send_json)

    async def send_snapshot_to(self, player: ConnectedPlayer, room: GameRoom) -> None:
        await game_session_service.send_snapshot_to(player, room, self._send_json)

    async def end_game(self, room: GameRoom, winner_color: str) -> None:
        await game_session_service.end_game(room, winner_color, self.db, self._send_json)

    async def handle_disconnect(self, player: ConnectedPlayer) -> None:
        await disconnect_service.handle_disconnect(
            player, self.matchmaking_queue, self.rooms, self.broadcast_room_state, self._run_resign_countdown
        )

    async def _run_resign_countdown(self, room: GameRoom, disconnected: ConnectedPlayer, opponent: Optional[ConnectedPlayer]) -> None:
        await disconnect_service.run_resign_countdown(room, disconnected, opponent, self._send_json, self.end_game)

