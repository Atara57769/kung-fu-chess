from dataclasses import is_dataclass, asdict
import asyncio
import json
import logging
import threading
import time
from typing import Optional, Callable
import websockets

from shared.constants import DEFAULT_HOST, DEFAULT_PORT, HEARTBEAT_INTERVAL
from shared.protocol.protocol import deserialize_snapshot, cell_to_algebraic, move_to_algebraic
from shared.models.color import Color
from shared.models.cell import Cell
from shared.models.game_over_result import GameOverResult
from shared.protocol import (
    MessageType, AuthMessage, AuthResponseMessage, HeartbeatMessage, MatchmakingMessage,
    LeaveMatchmakingMessage, MatchmakingStatusMessage, CreateRoomMessage, JoinRoomMessage,
    LeaveRoomMessage, RoomStateMessage, MoveMessage, JumpMessage, SnapshotMessage, CountdownMessage, GameOverMessage, ErrorMessage, parse_message,
)

from client.services.client_pubsub import ClientPubSub


logger = logging.getLogger(__name__)

class GameClient:
    """Handles network connection, heartbeat ping loops, and snapshot deserialization."""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        
        self.username: Optional[str] = None
        self.rating: int = 1200
        self.authenticated: bool = False
        
        self.room_state: Optional[dict] = None
        self.your_color: Optional[Color] = None  
        self.current_snapshot = None
        self.countdown_seconds: int = 0
        self.countdown_message: Optional[str] = None
        self.game_over_result: Optional[GameOverResult] = None
        self.error_message: Optional[str] = None
        
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.ws = None
        self.thread: Optional[threading.Thread] = None
        self.running: bool = False
        
        self.pubsub = ClientPubSub()
        self.on_update: Optional[Callable] = None
        self.message_handlers = {
            MessageType.AUTH_RESPONSE: self._handle_auth_response,
            MessageType.ROOM_STATE: self._handle_room_state,
            MessageType.SNAPSHOT: self._handle_snapshot,
            MessageType.COUNTDOWN: self._handle_countdown,
            MessageType.GAME_OVER: self._handle_game_over,
            MessageType.ERROR: self._handle_error,
            MessageType.MATCHMAKING_STATUS: self._handle_matchmaking_status,
        }

    def start(self) -> None:
        """Starts the background client thread with its own asyncio loop."""
        self.running = True
        self.thread = threading.Thread(target=self._run_network_loop, daemon=True)
        self.thread.start()
        
        time.sleep(0.2)

    def stop(self) -> None:
        """Closes sockets and halts the background network threads."""
        self.running = False
        if self.loop is not None and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread is not None:
            self.thread.join(timeout=1.0)

    def _run_network_loop(self) -> None:
        """Main thread entry point creating the local event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._main_network_coro())
        except Exception as e:
            logger.error(f"Network thread exception: {e}")
        finally:
            self.loop.close()

    async def _main_network_coro(self) -> None:
        """Coordinating coroutine establishing connections and running pings."""
        uri = f"ws://{self.host}:{self.port}"
        try:
            async with websockets.connect(uri) as ws:
                self.ws = ws
                logger.info(f"Connected to Game Server at {uri}")
                
                ping_task = asyncio.create_task(self._ping_loop())
                
                while self.running:
                    try:
                        raw_msg = await ws.recv()
                        await self._handle_incoming_message(raw_msg)
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Connection lost to server.")
                        break
                        
                ping_task.cancel()
        except Exception as e:
            logger.error(f"Failed connection to {uri}: {e}")
            self.error_message = "Could not connect to server."

    async def _ping_loop(self) -> None:
        """Sends periodic heartbeats to maintain connectivity."""
        try:
            while self.running:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._send_json_async(HeartbeatMessage())
        except asyncio.CancelledError:
            pass

    async def _handle_incoming_message(self, raw_msg: str) -> None:
        """Parses server JSON message types and updates state attributes."""
        try:
            data = json.loads(raw_msg)
            msg = parse_message(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            return

        handler = self.message_handlers.get(msg.type)
        if handler:
            handler(msg)
        else:
            logger.warning(f"Client received unhandled message type: {msg.type}")

        if self.on_update is not None:
            self.on_update()

    def _handle_auth_response(self, msg: AuthResponseMessage) -> None:
        self.authenticated = msg.success
        if self.authenticated:
            self.username = msg.username
            self.rating = msg.rating or 1200
        else:
            self.error_message = msg.error 
    def _handle_room_state(self, msg: RoomStateMessage) -> None:
        self.room_state = msg
        self.your_color = Color(msg.your_color) if msg.your_color else None
        self.game_over_result = None
        self.countdown_seconds = 0
        self.pubsub.publish(MessageType.ROOM_STATE, msg)

    def _handle_snapshot(self, msg: SnapshotMessage) -> None:
        self.current_snapshot = deserialize_snapshot(msg.data)
        self.pubsub.publish(MessageType.SNAPSHOT, self.current_snapshot)

    def _handle_countdown(self, msg: CountdownMessage) -> None:
        self.countdown_seconds = msg.seconds
        self.countdown_message = msg.message

    def _handle_game_over(self, msg: GameOverMessage) -> None:
        self.game_over_result = GameOverResult.from_message(msg)
        if self.your_color == Color.WHITE and msg.white_rating_change:
            self._update_elo_from_change(msg.white_rating_change)
        elif self.your_color == Color.BLACK and msg.black_rating_change:
            self._update_elo_from_change(msg.black_rating_change)


    def _handle_error(self, msg: ErrorMessage) -> None:
        self.error_message = msg.message
        self.pubsub.publish(MessageType.ERROR, msg)


    def _handle_matchmaking_status(self, msg: MatchmakingStatusMessage) -> None:
        self.pubsub.publish(MessageType.MATCHMAKING_STATUS, msg)


    def _update_elo_from_change(self, change_str: str) -> None:
        """Helper to parse updated ELO value from rating change suffix (e.g. ' (1200 -> 1216)')."""
        try:
            parts = change_str.split("->")
            if len(parts) == 2:
                self.rating = int(parts[1].replace(")", "").strip())
        except Exception:
            pass

    def _send_json(self, data: any) -> None:
        """Invokes raw socket write from external threads using loop scheduling."""
        if self.loop is not None and self.ws is not None:
            asyncio.run_coroutine_threadsafe(self._send_json_async(data), self.loop)

    async def _send_json_async(self, data: any) -> None:
        """Asynchronously writes json payload to raw websocket."""
        if is_dataclass(data):
            data = asdict(data)
        if self.ws is not None:
            try:
                await self.ws.send(json.dumps(data))
            except websockets.exceptions.ConnectionClosed:
                pass


    def authenticate(self, username, password) -> None:
        self.error_message = None
        self._send_json(AuthMessage(username=username, password=password))

    def enter_matchmaking(self) -> None:
        self._send_json(MatchmakingMessage())

    def leave_matchmaking(self) -> None:
        self._send_json(LeaveMatchmakingMessage())

    def create_room(self, room_id: Optional[str] = None) -> None:
        self._send_json(CreateRoomMessage(room_id=room_id))

    def join_room(self, room_id: str) -> None:
        self._send_json(JoinRoomMessage(room_id=room_id))

    def leave_room(self) -> None:
        self._send_json(LeaveRoomMessage())

    def send_move(self, from_cell: Cell, to_cell: Cell) -> None:
        height = self.current_snapshot.board.height if self.current_snapshot else 8
        move_str = move_to_algebraic(from_cell, to_cell, height)
        self._send_json(MoveMessage(data=move_str))

    def send_jump(self, cell: Cell) -> None:
        height = self.current_snapshot.board.height if self.current_snapshot else 8
        cell_str = cell_to_algebraic(cell, height)
        self._send_json(JumpMessage(data=cell_str))

