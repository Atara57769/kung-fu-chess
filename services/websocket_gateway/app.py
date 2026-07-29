import os
import json
import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Set, Optional, List
import websockets
from websockets.exceptions import ConnectionClosed

from shared.constants import DEFAULT_RATING
from shared.protocol import (
    MessageType, serialize_message, ErrorMessage, AuthResponseMessage
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] WS Gateway: %(message)s")
logger = logging.getLogger("WSGateway")

GATEWAY_ID = os.getenv("GATEWAY_ID", "ws_gw_1")
PORT = int(os.getenv("PORT", "8001"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

nats_bus = NatsBus(url=NATS_URL)


import redis.asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return redis_client


@dataclass
class GatewaySession:
    authenticated: bool = False
    username: Optional[str] = None
    room_id: Optional[str] = None
    rating: int = DEFAULT_RATING


active_sockets: Dict[Any, GatewaySession] = {}
room_subscriptions: Dict[str, Set[Any]] = {}


async def handle_nats_game_state(data: GameStatePayload, reply_to: Optional[str]) -> None:
    room_id = data.room_id
    target_username = data.target_username
    payload = data.state

    if not payload:
        return

    serialized = json.dumps(payload) if isinstance(payload, dict) else str(payload)

    if target_username:
        for ws, info in list(active_sockets.items()):
            if info.username == target_username:
                if room_id and info.room_id != room_id:
                    info.room_id = room_id
                    room_subscriptions.setdefault(room_id, set()).add(ws)
                try:
                    await ws.send(serialized)
                except Exception:
                    pass
    elif room_id and room_id in room_subscriptions:
        for ws in list(room_subscriptions[room_id]):
            try:
                await ws.send(serialized)
            except Exception:
                pass


async def handle_nats_room_event(data: Any, reply_to: Optional[str]) -> None:
    room_id = getattr(data, "room_id", None)
    host = getattr(data, "host", None)
    username = getattr(data, "username", None)

    if not room_id:
        return

    target_user = host or username
    if target_user:
        for ws, info in list(active_sockets.items()):
            if info.username == target_user:
                info.room_id = room_id
                room_subscriptions.setdefault(room_id, set()).add(ws)

    serialized = json.dumps(asdict(data)) if hasattr(data, "__dataclass_fields__") else (json.dumps(data) if isinstance(data, dict) else str(data))

    if room_id in room_subscriptions:
        for ws in list(room_subscriptions[room_id]):
            try:
                await ws.send(serialized)
            except Exception:
                pass


async def handle_client_message(ws: Any, raw_msg: str) -> None:
    info = active_sockets.get(ws)
    if not info:
        info = GatewaySession()
        active_sockets[ws] = info

    try:
        data = json.loads(raw_msg)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received from WebSocket client.")
        return

    msg_type = data.get("type")

    if msg_type in (MessageType.AUTH, MessageType.AUTH.value):
        username = data.get("username")
        token = data.get("token")
        password = data.get("password")

        authenticated = False
        user_rating = DEFAULT_RATING

        if username and (password or token):
            try:
                auth_req = AuthLoginPayload(username=username, password=password, token=token)
                reply = await nats_bus.request(AUTH_LOGIN, auth_req, timeout=3.0)
                if reply.get("success"):
                    authenticated = True
                    user_rating = reply.get("rating", DEFAULT_RATING)
            except Exception as e:
                logger.warning("NATS Auth request failed: %s. Accepting connection for %s", e, username)
                authenticated = True

        if authenticated:
            info.authenticated = True
            info.username = username
            info.rating = user_rating
            resp = serialize_message(AuthResponseMessage(success=True, username=username, rating=user_rating))
            await ws.send(resp)
            logger.info("Client '%s' authenticated on WS Gateway", username)

            connected_dto = PlayerConnectedPayload(gateway_id=GATEWAY_ID, username=username)
            await nats_bus.publish(PLAYER_CONNECTED, connected_dto)
        else:
            resp = serialize_message(AuthResponseMessage(success=False, error="Invalid credentials or session token."))
            await ws.send(resp)
        return

    if not info.authenticated:
        await ws.send(serialize_message(ErrorMessage(message="Unauthorized connection.")))
        return

    username = info.username
    room_id = data.get("room_id") or info.room_id

    if msg_type in (MessageType.CREATE_ROOM, MessageType.CREATE_ROOM.value) and not room_id:
        room_id = f"room_{os.urandom(4).hex()}"
        data["room_id"] = room_id

    target_server = None
    if room_id:
        info.room_id = room_id
        room_subscriptions.setdefault(room_id, set()).add(ws)
        try:
            redis = await get_redis()
            target_server = await redis.hget("room_routes", room_id)
        except Exception as e:
            logger.warning("Failed to query room_routes from Redis: %s", e)

    cmd_dto = GameCommandPayload(
        room_id=room_id,
        username=username,
        gateway_id=GATEWAY_ID,
        data=data,
        target_server=target_server
    )
    await nats_bus.publish(GAME_COMMAND, cmd_dto)
    if target_server:
        await nats_bus.publish(f"game.command.{target_server}", cmd_dto)


async def handle_connection(ws: Any, path: str = None) -> None:
    active_sockets[ws] = GatewaySession()
    logger.info("New client connected to WebSocket Gateway.")
    try:
        async for message in ws:
            await handle_client_message(ws, message)
    except ConnectionClosed:
        logger.info("Client disconnected from WebSocket Gateway.")
    finally:
        info = active_sockets.pop(ws, None)
        username = info.username if info else None
        room_id = info.room_id if info else None

        if room_id and room_id in room_subscriptions:
            room_subscriptions[room_id].discard(ws)
            if not room_subscriptions[room_id]:
                del room_subscriptions[room_id]

        if username:
            disconnected_dto = PlayerDisconnectedPayload(gateway_id=GATEWAY_ID, username=username)
            await nats_bus.publish(PLAYER_DISCONNECTED, disconnected_dto)


async def main() -> None:
    await nats_bus.connect()
    logger.info("WS Gateway subscribing to NATS topics...")
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
