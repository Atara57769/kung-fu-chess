import os
import json
import asyncio
import logging
from typing import Dict, Any, Set, Optional
import websockets
from websockets.exceptions import ConnectionClosed
import redis.asyncio as aioredis

from shared.constants import DEFAULT_RATING, ROOM_STATUS_WAITING
from shared.protocol import (
    MessageType,
    serialize_message,
    ErrorMessage,
    AuthResponseMessage,
    RoomStateMessage
)
from shared.message_contracts.subjects import (
    AUTH_LOGIN, GAME_COMMAND, GAME_STATE, GAME_FINISHED, GAME_EVENTS,
    PLAYER_CONNECTED, PLAYER_DISCONNECTED, ROOM_CREATED, ROOM_JOINED, ROOM_UPDATED
)
from shared.message_contracts.contracts import (
    AuthLoginPayload, GameCommandPayload, PlayerConnectedPayload, PlayerDisconnectedPayload,
    GameStatePayload, RoomCreatedPayload
)
from shared.message_contracts.nats_client import NatsBus
from server.database.sqlite_db_manager import SQLiteDBManager
from server.database.postgres_db_manager import PostgresDBManager
from server.services.auth_service import authenticate_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] WS Gateway: %(message)s")
logger = logging.getLogger("WSGateway")

GATEWAY_ID = os.getenv("GATEWAY_ID", "ws_gw_1")
PORT = int(os.getenv("PORT", "8001"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

db_manager = PostgresDBManager()

nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None

active_sockets: Dict[Any, Dict[str, Any]] = {}
room_subscriptions: Dict[str, Set[Any]] = {}


async def handle_nats_game_state(data: GameStatePayload, reply_to: Optional[str]) -> None:
    room_id = getattr(data, "room_id", None)
    target_username = getattr(data, "target_username", None)
    payload = getattr(data, "state", None)

    if not payload:
        return

    serialized = json.dumps(payload) if isinstance(payload, dict) else str(payload)

    # Automatically map active WS socket for target_username to room_id
    if room_id and target_username:
        for ws, info in list(active_sockets.items()):
            if info.get("username") == target_username:
                info["room_id"] = room_id
                if room_id not in room_subscriptions:
                    room_subscriptions[room_id] = set()
                room_subscriptions[room_id].add(ws)

    if target_username:
        for ws, info in list(active_sockets.items()):
            if info.get("username") == target_username:
                try:
                    await ws.send(serialized)
                except Exception:
                    pass


async def handle_nats_room_event(data: RoomCreatedPayload, reply_to: Optional[str]) -> None:
    room_id = getattr(data, "room_id", None)
    host = getattr(data, "host", None)
    username = getattr(data, "username", None)

    if not room_id:
        return

    # Associate host socket with room_id on room creation
    if host:
        for ws, info in list(active_sockets.items()):
            if info.get("username") == host:
                info["room_id"] = room_id
                if room_id not in room_subscriptions:
                    room_subscriptions[room_id] = set()
                room_subscriptions[room_id].add(ws)

    # Associate joining user socket with room_id on room join
    if username:
        for ws, info in list(active_sockets.items()):
            if info.get("username") == username:
                info["room_id"] = room_id
                if room_id not in room_subscriptions:
                    room_subscriptions[room_id] = set()
                room_subscriptions[room_id].add(ws)

    # Fetch room metadata from Redis
    white_player = host or username
    black_player = None
    spectators: List[str] = []

    if redis_client:
        raw_meta = await redis_client.get(f"room_meta:{room_id}")
        if raw_meta:
            try:
                meta = json.loads(raw_meta)
                players = meta.get("players", [])
                white_player = players[0] if len(players) > 0 else (host or username)
                black_player = players[1] if len(players) > 1 else None
            except Exception:
                pass

    if room_id in room_subscriptions:
        for ws in list(room_subscriptions[room_id]):
            info = active_sockets.get(ws, {})
            u = info.get("username")
            your_color = "w" if u == white_player else ("b" if u == black_player else None)

            state_msg = RoomStateMessage(
                room_id=room_id,
                status=ROOM_STATUS_WAITING,
                white=white_player,
                black=black_player,
                spectators=spectators,
                your_color=your_color
            )
            serialized = serialize_message(state_msg)
            try:
                await ws.send(serialized)
            except Exception:
                pass


async def handle_client_message(ws: Any, raw_msg: str) -> None:
    info = active_sockets.get(ws, {})
    try:
        data = json.loads(raw_msg)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received from WebSocket client.")
        return

    msg_type = data.get("type")

    if msg_type == MessageType.AUTH:
        username = data.get("username")
        token = data.get("token")
        password = data.get("password")

        authenticated = False
        user_rating = DEFAULT_RATING

        if token and redis_client:
            stored_user = await redis_client.get(f"session:{token}")
            if stored_user and stored_user == username:
                authenticated = True

        if not authenticated and username and password:
            try:
                auth_req = AuthLoginPayload(username=username, password=password)
                reply = await nats_bus.request(AUTH_LOGIN, auth_req, timeout=3.0)
                if reply.get("success"):
                    authenticated = True
                    user_rating = reply.get("rating", DEFAULT_RATING)
            except Exception:
                success, user_info, err = authenticate_user(username, password, db_manager)
                if success and user_info:
                    authenticated = True
                    user_rating = user_info.rating

        if authenticated:
            info["authenticated"] = True
            info["username"] = username
            info["rating"] = user_rating
            resp = serialize_message(AuthResponseMessage(success=True, username=username, rating=user_rating))
            await ws.send(resp)
            logger.info("Client '%s' authenticated on WS Gateway", username)

            connected_dto = PlayerConnectedPayload(gateway_id=GATEWAY_ID, username=username)
            await nats_bus.publish(PLAYER_CONNECTED, connected_dto)
        else:
            resp = serialize_message(AuthResponseMessage(success=False, error="Invalid credentials or session token."))
            await ws.send(resp)
        return

    if not info.get("authenticated"):
        await ws.send(serialize_message(ErrorMessage(message="Unauthorized connection.")))
        return

    username = info.get("username")
    room_id = data.get("room_id") or info.get("room_id")

    if msg_type == MessageType.CREATE_ROOM and not room_id:
        room_id = f"room_{os.urandom(4).hex()}"
        data["room_id"] = room_id

    if room_id:
        info["room_id"] = room_id
        if room_id not in room_subscriptions:
            room_subscriptions[room_id] = set()
        room_subscriptions[room_id].add(ws)

    cmd_dto = GameCommandPayload(
        room_id=room_id,
        username=username,
        gateway_id=GATEWAY_ID,
        data=data
    )
    await nats_bus.publish(GAME_COMMAND, cmd_dto)


async def handle_connection(ws: Any, path: str = None) -> None:
    active_sockets[ws] = {"authenticated": False, "username": None, "room_id": None}
    logger.info("New client connected to WebSocket Gateway.")
    try:
        async for message in ws:
            await handle_client_message(ws, message)
    except ConnectionClosed:
        logger.info("Client disconnected from WebSocket Gateway.")
    finally:
        info = active_sockets.pop(ws, {})
        username = info.get("username")
        room_id = info.get("room_id")

        if room_id and room_id in room_subscriptions:
            room_subscriptions[room_id].discard(ws)
            if not room_subscriptions[room_id]:
                del room_subscriptions[room_id]

        if username:
            disconnected_dto = PlayerDisconnectedPayload(gateway_id=GATEWAY_ID, username=username)
            await nats_bus.publish(PLAYER_DISCONNECTED, disconnected_dto)


async def main() -> None:
    global redis_client
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    await nats_bus.connect()
    logger.info("WS Gateway subscribing to NATS game state subjects...")
    await nats_bus.subscribe(GAME_STATE, handle_nats_game_state, dto_class=GameStatePayload)
    await nats_bus.subscribe(GAME_FINISHED, handle_nats_game_state, dto_class=GameStatePayload)
    await nats_bus.subscribe(GAME_EVENTS, handle_nats_game_state, dto_class=GameStatePayload)
    await nats_bus.subscribe(ROOM_CREATED, handle_nats_room_event, dto_class=RoomCreatedPayload)
    await nats_bus.subscribe(ROOM_JOINED, handle_nats_room_event, dto_class=RoomCreatedPayload)
    await nats_bus.subscribe(ROOM_UPDATED, handle_nats_room_event, dto_class=RoomCreatedPayload)

    logger.info("Starting WebSocket Gateway on ws://0.0.0.0:%d...", PORT)
    async with websockets.serve(handle_connection, "0.0.0.0", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket Gateway shut down.")
