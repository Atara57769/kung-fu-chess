"""
Distributed Game Client for Kung-Fu Chess Microservices Architecture.
Handles REST communication with API Gateway and real-time WebSockets with WS Gateway using DTO Dataclasses.
"""

import json
import logging
import threading
import time
import urllib.request
import urllib.parse
import asyncio
import ssl
from typing import Optional, Callable, Dict, Any, List
import websockets

from shared.constants import DEFAULT_HOST, DEFAULT_PORT, HEARTBEAT_INTERVAL, DEFAULT_RATING, ResponseStatus
from shared.models.color import Color
from shared.models.cell import Cell
from shared.security.ssl_config import get_client_ssl_context
from shared.protocol import (
    MessageType, AuthMessage, AuthResponseMessage, HeartbeatMessage, MatchmakingMessage,
    LeaveMatchmakingMessage, MatchmakingStatusMessage, MatchmakingTimeoutMessage, CreateRoomMessage, JoinRoomMessage,
    LeaveRoomMessage, RoomStateMessage, MoveMessage, JumpMessage, SnapshotMessage, CountdownMessage,
    GameOverMessage, ErrorMessage, serialize_message, deserialize_message
)
from shared.protocol.protocol import deserialize_snapshot
from shared.message_contracts.contracts import (
    AuthLoginPayload, MatchmakingRequestPayload, AuthResponsePayload,
    MatchmakingResponsePayload, RoomListResponsePayload,
    RoomInfoDTO, HealthStatusPayload, RoomCreatePayload,
    RoomCreatedPayload, RoomJoinPayload, RoomLeavePayload
)
from client.network.base_client import BaseGameClient
from client.services.client_pubsub import ClientPubSub

logger = logging.getLogger(__name__)


class DistributedGameClient(BaseGameClient):
    """Network client for Distributed Microservices Architecture.
    Interfaces with API Gateway (REST) and WebSocket Gateway (Real-Time WS) using DTO Dataclasses.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        ws_host: str = DEFAULT_HOST,
        ws_port: int = 8001,
        use_ssl: bool = True,
        verify_ssl: bool = False,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl

        if use_ssl:
            self.ssl_context = ssl_context or get_client_ssl_context(verify_ssl=verify_ssl)
            if api_url.startswith("http://"):
                api_url = "https://" + api_url[len("http://"):]
        else:
            self.ssl_context = None

        self.api_url = api_url.rstrip('/')
        self.ws_host = ws_host
        self.ws_port = ws_port

        self.username: Optional[str] = None
        self.token: Optional[str] = None
        self.rating: int = DEFAULT_RATING
        self.authenticated: bool = False

        self.room_state: Optional[dict] = None
        self.your_color: Optional[Color] = None
        self.current_snapshot = None
        self.countdown_seconds: int = 0
        self.countdown_message: Optional[str] = None
        self.game_over_result: Optional[Any] = None
        self.error_message: Optional[str] = None

        self.pubsub = ClientPubSub()
        self.on_update: Optional[Callable] = None

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.ws = None
        self.thread: Optional[threading.Thread] = None
        self.running: bool = False

        self.message_handlers = {
            MessageType.AUTH_RESPONSE: self._handle_auth_response,
            MessageType.HEARTBEAT_ACK: lambda msg: None,
            MessageType.ROOM_STATE: self._handle_room_state,
            MessageType.SNAPSHOT: self._handle_snapshot,
            MessageType.COUNTDOWN: self._handle_countdown,
            MessageType.GAME_OVER: self._handle_game_over,
            MessageType.ERROR: self._handle_error,
            MessageType.MATCHMAKING_STATUS: self._handle_matchmaking_status,
            MessageType.MATCHMAKING_TIMEOUT: self._handle_matchmaking_timeout,
        }


    def health(self) -> HealthStatusPayload:
        """Calls GET /healthz endpoint on API Gateway returning HealthStatusPayload DTO."""
        url = f"{self.api_url}/healthz"
        res = self._http_get(url)
        return HealthStatusPayload(**res)

    def login(self, username: str, password: str) -> AuthResponsePayload:
        """Calls POST /auth/login endpoint on API Gateway returning AuthResponsePayload DTO and saving session token."""
        url = f"{self.api_url}/auth/login"
        req_dto = AuthLoginPayload(username=username, password=password)
        res = self._http_post(url, req_dto)
        auth_resp = AuthResponsePayload(**res)
        if auth_resp.status == ResponseStatus.SUCCESS.value or auth_resp.status == ResponseStatus.SUCCESS:
            self.username = auth_resp.username
            self.token = auth_resp.token
            self.rating = auth_resp.rating
        return auth_resp

    def list_rooms(self) -> RoomListResponsePayload:
        """Calls GET /rooms endpoint on API Gateway returning RoomListResponsePayload DTO."""
        url = f"{self.api_url}/rooms"
        res = self._http_get(url)
        room_dtos = [RoomInfoDTO(**r) for r in res["rooms"]]
        return RoomListResponsePayload(rooms=room_dtos)

    def get_history(self) -> Dict[str, Any]:
        """Calls GET /history endpoint on API Gateway."""
        url = f"{self.api_url}/history"
        if self.username:
            url += f"?username={urllib.parse.quote(self.username)}"
        return self._http_get(url)

    def _http_get(self, url: str) -> Dict[str, Any]:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=self.ssl_context) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _http_post(self, url: str, payload: Any) -> Dict[str, Any]:
        payload_dict = payload.to_dict() if hasattr(payload, "to_dict") else payload
        data = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, context=self.ssl_context) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def start(self) -> None:
        """Starts background network thread establishing WS connection to WS Gateway."""
        self.running = True
        self.thread = threading.Thread(target=self._run_network_loop, daemon=True)
        self.thread.start()
        time.sleep(0.2)

    def stop(self) -> None:
        """Halts network thread and closes WebSocket session."""
        self.running = False
        if self.loop is not None and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread is not None:
            self.thread.join(timeout=1.0)

    def _run_network_loop(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._main_network_coro())
        except Exception as e:
            logger.error(f"Distributed WS thread error: {e}")
        finally:
            self.loop.close()

    async def _main_network_coro(self) -> None:
        scheme = "wss" if self.ssl_context else "ws"
        uri = f"{scheme}://{self.ws_host}:{self.ws_port}"
        try:
            async with websockets.connect(uri, ssl=self.ssl_context) as ws:
                self.ws = ws
                logger.info(f"Connected to WebSocket Gateway at {uri}")

                if self.username:
                    await self._send_json_async(AuthMessage(username=self.username, token=self.token))

                ping_task = asyncio.create_task(self._ping_loop())

                while self.running:
                    try:
                        raw_msg = await ws.recv()
                        await self._handle_incoming_message(raw_msg)
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Connection to WebSocket Gateway closed.")
                        break

                ping_task.cancel()
        except Exception as e:
            logger.error(f"Failed connection to {uri}: {e}")
            self.error_message = "Could not connect to WebSocket Gateway."

    async def _ping_loop(self) -> None:
        try:
            while self.running:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._send_json_async(HeartbeatMessage())
        except asyncio.CancelledError:
            pass


    async def _handle_incoming_message(self, raw_msg: str) -> None:
        try:
            msg = deserialize_message(raw_msg)
        except (ValueError, KeyError):
            return

        handler = self.message_handlers.get(msg.type)
        if handler:
            handler(msg)
        else:
            logger.warning(f"Distributed Client received unhandled message type: {msg.type}")

        if self.on_update is not None:
            self.on_update()

    def _handle_auth_response(self, msg: AuthResponseMessage) -> None:
        self.authenticated = msg.success
        if self.authenticated:
            self.username = msg.username
            self.rating = msg.rating or DEFAULT_RATING
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
        self.game_over_result = msg
        if self.your_color == Color.WHITE and msg.white_rating is not None:
            self.rating = msg.white_rating
        elif self.your_color == Color.BLACK and msg.black_rating is not None:
            self.rating = msg.black_rating

    def _handle_error(self, msg: ErrorMessage) -> None:
        self.error_message = msg.message
        self.pubsub.publish(MessageType.ERROR, msg)

    def _handle_matchmaking_status(self, msg: MatchmakingStatusMessage) -> None:
        self.pubsub.publish(MessageType.MATCHMAKING_STATUS, msg)

    def _handle_matchmaking_timeout(self, msg: MatchmakingTimeoutMessage) -> None:
        self.pubsub.publish(MessageType.MATCHMAKING_TIMEOUT, msg)

    def _send_json(self, data: Any) -> None:
        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(self._send_json_async(data), self.loop)

    async def _send_json_async(self, data: Any) -> None:
        for _ in range(50):
            if self.ws is not None:
                try:
                    await self.ws.send(serialize_message(data))
                    return
                except websockets.exceptions.ConnectionClosed:
                    return
            await asyncio.sleep(0.1)


    def authenticate(self, username: str, password_or_token: str) -> None:
        """Authenticates user via REST API /auth/login (auto-registering if non-existent) to obtain token, then sends AuthMessage over WS."""
        self.error_message = None
        if not self.token:
            try:
                auth_resp = self.login(username, password_or_token)
                if auth_resp.status in (ResponseStatus.SUCCESS.value, ResponseStatus.SUCCESS):
                    self.authenticated = True
            except Exception as e:
                logger.warning(f"REST /auth/login call in authenticate failed: {e}")

        self._send_json(AuthMessage(username=username, password=password_or_token, token=self.token))

    def join_matchmaking(self) -> MatchmakingResponsePayload:
        """Joins matchmaking by calling API Gateway REST endpoint POST /matchmaking/join."""
        url = f"{self.api_url}/matchmaking/join"
        req_dto = MatchmakingRequestPayload(action="join", username=self.username or "", token=self.token, rating=self.rating)
        res = self._http_post(url, req_dto)
        return MatchmakingResponsePayload(**res)

    def leave_matchmaking(self) -> MatchmakingResponsePayload:
        """Leaves matchmaking by calling API Gateway REST endpoint POST /matchmaking/leave."""
        url = f"{self.api_url}/matchmaking/leave"
        req_dto = MatchmakingRequestPayload(action="leave", username=self.username or "", token=self.token)
        res = self._http_post(url, req_dto)
        return MatchmakingResponsePayload(**res)

    def create_room(self, room_id: Optional[str] = None) -> RoomCreatedPayload:
        """Creates a room by calling API Gateway REST endpoint POST /rooms/create."""
        url = f"{self.api_url}/rooms/create"
        req_dto = RoomCreatePayload(room_id=room_id or "", host=self.username or "anonymous")
        res = self._http_post(url, req_dto)
        return RoomCreatedPayload(**res)

    def join_room(self, room_id: str) -> RoomJoinPayload:
        """Joins a room by calling API Gateway REST endpoint POST /rooms/join."""
        url = f"{self.api_url}/rooms/join"
        req_dto = RoomJoinPayload(room_id=room_id, username=self.username or "anonymous")
        res = self._http_post(url, req_dto)
        return RoomJoinPayload(**res)

    def leave_room(self, room_id: str = "") -> RoomLeavePayload:
        """Leaves room by calling API Gateway REST endpoint POST /rooms/leave."""
        url = f"{self.api_url}/rooms/leave"
        req_dto = RoomLeavePayload(room_id=room_id, username=self.username or "anonymous")
        res = self._http_post(url, req_dto)
        return RoomLeavePayload(**res)

    def send_move(self, from_cell: Cell, to_cell: Cell) -> None:
        self._send_json(MoveMessage(from_cell=from_cell, to_cell=to_cell))

    def send_jump(self, cell: Cell) -> None:
        self._send_json(JumpMessage(cell=cell))
