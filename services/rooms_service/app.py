import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
from shared.constants import ResponseStatus, ROOM_STATUS_ACTIVE
from shared.message_contracts.subjects import (ROOM_CREATE, ROOM_CREATED, ROOM_JOIN, ROOM_JOINED, ROOM_LEAVE, ROOM_UPDATED, GAME_ALLOCATE)
from shared.message_contracts.contracts import (
    RoomCreatePayload, RoomCreatedPayload, RoomJoinPayload, RoomLeavePayload, GameAllocatePayload
)
from shared.message_contracts.nats_client import NatsBus
from server.network.models import GameRoom, ConnectedPlayer
from server.services.room_service import RoomService, RoomJoinEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Rooms Service: %(message)s")
logger = logging.getLogger("RoomsService")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None

rooms_domain: Dict[str, GameRoom] = {}
room_service = RoomService()


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return redis_client


async def handle_room_create(data: RoomCreatePayload, reply_to: Optional[str]) -> Optional[RoomCreatedPayload]:
    room_id = data.room_id
    host_name = data.host or data.username or "anonymous"
    shard_id = data.shard_id or "unassigned"

    host_player = ConnectedPlayer(ws=None, ip_address="remote")
    host_player.username = host_name
    host_player.authenticated = True

    await room_service.create_room(host_player, rooms_domain, room_id=room_id)
    created_room_id = host_player.room_id or room_id or "room_1"
    redis = await get_redis()

    room_meta = {
        "room_id": created_room_id,
        "host": host_name,
        "players": [host_name],
        "created_at": time.time(),
        "status": ResponseStatus.CREATED.value
    }
    await redis.hset("room_routes", created_room_id, shard_id)
    await redis.set(f"room_meta:{created_room_id}", json.dumps(room_meta))

    logger.info("Room '%s' created by '%s' via RoomService", created_room_id, host_name)

    created_dto = RoomCreatedPayload(
        room_id=created_room_id,
        host=host_name,
        created_at=room_meta["created_at"]
    )
    await nats_bus.publish(ROOM_CREATED, created_dto)
    return created_dto


async def handle_room_join(data: RoomJoinPayload, reply_to: Optional[str]) -> Optional[RoomJoinPayload]:
    room_id = data.room_id
    username = data.username

    if not room_id or not username:
        return None

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.authenticated = True

    if room_id not in rooms_domain:
        rooms_domain[room_id] = GameRoom(room_id=room_id)

    event, room = await room_service.join_room(player, room_id, rooms_domain)

    if event == RoomJoinEvent.NOT_FOUND:
        return None

    redis = await get_redis()
    raw_meta = await redis.get(f"room_meta:{room_id}")
    meta = json.loads(raw_meta) if raw_meta else {"room_id": room_id, "players": []}

    if username not in meta.get("players", []):
        meta.setdefault("players", []).append(username)
    
    if event == RoomJoinEvent.GAME_CAN_START:
        meta["status"] = ROOM_STATUS_ACTIVE
        
    await redis.set(f"room_meta:{room_id}", json.dumps(meta))

    logger.info("User '%s' joined room '%s' (Event: %s)", username, room_id, event.name)

    join_dto = RoomJoinPayload(room_id=room_id, username=username)
    await nats_bus.publish(ROOM_JOINED, join_dto)
    await nats_bus.publish(ROOM_UPDATED, join_dto)

    if event == RoomJoinEvent.GAME_CAN_START and room and room.white_player and room.black_player:
        allocate_dto = GameAllocatePayload(
            room_id=room_id,
            player1=room.white_player.username,
            player2=room.black_player.username
        )
        logger.info("Room '%s' has 2 players. Publishing GAME_ALLOCATE for %s vs %s",
                    room_id, room.white_player.username, room.black_player.username)
        await nats_bus.publish(GAME_ALLOCATE, allocate_dto)

    return join_dto


async def handle_room_leave(data: RoomLeavePayload, reply_to: Optional[str]) -> Optional[RoomLeavePayload]:
    room_id = data.room_id
    username = data.username

    if not room_id or not username:
        return None

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.room_id = room_id

    await room_service.leave_room(player, rooms_domain)

    redis = await get_redis()
    raw_meta = await redis.get(f"room_meta:{room_id}")
    if raw_meta:
        meta = json.loads(raw_meta)
        if username in meta.get("players", []):
            meta["players"].remove(username)
            await redis.set(f"room_meta:{room_id}", json.dumps(meta))

        logger.info("User '%s' left room '%s'", username, room_id)
        leave_dto = RoomLeavePayload(room_id=room_id, username=username)
        await nats_bus.publish(ROOM_UPDATED, leave_dto)
        return leave_dto

    return None


async def main():
    await nats_bus.connect()
    logger.info("Rooms Service initialized. Subscribing to room subjects...")
    await nats_bus.subscribe(ROOM_CREATE, handle_room_create, dto_class=RoomCreatePayload)
    await nats_bus.subscribe(ROOM_JOIN, handle_room_join, dto_class=RoomJoinPayload)
    await nats_bus.subscribe(ROOM_LEAVE, handle_room_leave, dto_class=RoomLeavePayload)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Rooms Service shutting down.")
