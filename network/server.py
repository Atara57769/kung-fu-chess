import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional
import websockets
from websockets.exceptions import ConnectionClosed
from constants import (DEFAULT_HOST, DEFAULT_PORT, HEARTBEAT_TIMEOUT, DISCONNECT_COUNTDOWN, DEFAULT_BOARD_LAYOUT)
from ui.ui_config import TIME_STEP_MS
from database.db_manager import DBManager
from network.models import ConnectedPlayer, GameRoom
from network.services.game_services import elo_service, game_session_service, disconnect_service
from network.services.network_services import connection_handler, auth_service, matchmaking_service, room_service

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

    async def start(self) -> None:
        """Starts the WebSocket server listening loop."""
        async def _internal_handler(ws, path=None):
            await connection_handler.connection_handler(ws, self)
            
        async with websockets.serve(_internal_handler, self.host, self.port):
            logger.info(f"Kung-Fu Chess Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()

    async def dispatch_message(self, player: ConnectedPlayer, raw_msg: str) -> None:
        """Decodes JSON message and dispatches it to the correct action handler."""
        player.last_heartbeat = time.time()
        try:
            data = json.loads(raw_msg)
        except json.JSONDecodeError:
            logger.warning("Received invalid non-JSON message.")
            return

        msg_type = data.get("type")
        if msg_type == "auth":
            await auth_service.handle_auth(player, data, self.db, self._send_json)
        elif not player.authenticated:
            await self._send_json(player.ws, {"type": "error", "message": "Unauthorized client."})
        else:
            await self._handle_authenticated_message(player, msg_type, data)

    async def _handle_authenticated_message(self, player: ConnectedPlayer, msg_type: str, data: dict) -> None:
        """Dispatches authenticated client message command to its matching service."""
        if msg_type == "matchmaking":
            await matchmaking_service.add_to_matchmaking(player, self.matchmaking_queue, self._send_json, self._start_matched_game)
        elif msg_type == "leave_matchmaking":
            await matchmaking_service.remove_from_matchmaking(player, self.matchmaking_queue, self._send_json)
        elif msg_type == "create_room":
            await room_service.create_custom_room(player, self.rooms, self._send_json, self.broadcast_room_state)
        elif msg_type == "join_room":
            await room_service.join_custom_room(
                player, data.get("room_id", ""), self.rooms, self._send_json,
                self.broadcast_room_state, self._start_game_session, self.send_snapshot_to
            )
        elif msg_type == "move":
            await game_session_service.process_game_move(player, data.get("data", ""), self.rooms, self.broadcast_snapshot)
        elif msg_type == "jump":
            await game_session_service.process_game_jump(player, data.get("data", ""), self.rooms, self.broadcast_snapshot)
        elif msg_type == "leave_room":
            await room_service.handle_leave_room(player, self.rooms, self._send_json, self.broadcast_room_state)
        elif msg_type == "heartbeat":
            await self._send_json(player.ws, {"type": "heartbeat_ack"})

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

        # Determine colors randomly
        if random.choice([True, False]):
            room.white_player = p1
            room.black_player = p2
        else:
            room.white_player = p2
            room.black_player = p1

        room.white_player.room_id = room_id
        room.white_player.color = "w"
        room.black_player.room_id = room_id
        room.black_player.color = "b"

        logger.info(f"Matched Game started in Room {room_id}: White={room.white_player.username}, Black={room.black_player.username}")
        await self._start_game_session(room)

    async def _start_game_session(self, room: GameRoom) -> None:
        await game_session_service.start_game_session(room, self.broadcast_room_state, self._room_tick_loop)

    async def _room_tick_loop(self, room: GameRoom) -> None:
        """Authoritative real-time progression ticking game state."""
        tick_interval = TIME_STEP_MS / 1000.0
        try:
            while room.status == "active":
                await asyncio.sleep(tick_interval)
                
                room.game_engine.wait(room.state, TIME_STEP_MS)
                
                if room.state.game_over:
                    winner_token = room.state.winner if hasattr(room.state, "winner") else None
                    if not winner_token:
                        has_w_king = False
                        has_b_king = False
                        for row in room.state.board.grid:
                            for p in row:
                                if p is not None and p.kind == "K":
                                    if p.color == "w": has_w_king = True
                                    elif p.color == "b": has_b_king = True
                        if has_w_king and not has_b_king:
                            winner_token = "w"
                        elif has_b_king and not has_w_king:
                            winner_token = "b"
                    
                    winner_color = "white" if winner_token == "w" else ("black" if winner_token == "b" else "draw")
                    await self.end_game(room, winner_color)
                    break
                    
                await self.broadcast_snapshot(room)
        except asyncio.CancelledError:
            pass

    async def broadcast_room_state(self, room: GameRoom) -> None:
        await room_service.broadcast_room_state(room, self._send_json)

    async def broadcast_snapshot(self, room: GameRoom) -> None:
        await game_session_service.broadcast_snapshot(room, self._send_json)

    async def send_snapshot_to(self, player: ConnectedPlayer, room: GameRoom) -> None:
        await game_session_service.send_snapshot_to(player, room, self._send_json)

    async def end_game(self, room: GameRoom, winner_color: str) -> None:
        await game_session_service.end_game(room, winner_color, self.db, elo_service.calculate_elo, self._send_json)

    async def handle_disconnect(self, player: ConnectedPlayer) -> None:
        await disconnect_service.handle_disconnect(
            player, self.matchmaking_queue, self.rooms, self.broadcast_room_state, self._run_resign_countdown
        )

    async def _run_resign_countdown(self, room: GameRoom, disconnected: ConnectedPlayer, opponent: Optional[ConnectedPlayer]) -> None:
        await disconnect_service.run_resign_countdown(room, disconnected, opponent, self._send_json, self.end_game)
