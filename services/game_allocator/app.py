import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis

from shared.message_contracts.subjects import (
    MATCHMAKING_MATCH_FOUND, GAME_ALLOCATE, GAME_ASSIGNED
)
from shared.message_contracts.contracts import GameAssignedPayload, GameAllocatePayload
from shared.message_contracts.nats_client import NatsBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Game Allocator: %(message)s")
logger = logging.getLogger("GameAllocator")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
GAME_SERVERS = os.getenv("GAME_SERVERS", "game_server_1,game_server_2").split(",")

nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None
server_index = 0


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return redis_client


def select_next_game_server() -> str:
    global server_index
    target = GAME_SERVERS[server_index % len(GAME_SERVERS)]
    server_index += 1
    return target


async def handle_match_found_or_allocate(data: GameAllocatePayload, reply_to: Optional[str]) -> Optional[GameAssignedPayload]:
    room_id = data.room_id
    player1 = data.player1
    player2 = data.player2

    if not room_id or not player1 or not player2:
        logger.warning("Received invalid allocation payload: %s", data)
        return None

    target_server = select_next_game_server()
    logger.info("Allocating room '%s' (%s vs %s) to Game Server '%s'", room_id, player1, player2, target_server)

    redis = await get_redis()
    await redis.hset("room_routes", room_id, target_server)

    assigned_dto = GameAssignedPayload(
        room_id=room_id,
        game_server_id=target_server,
        player1=player1,
        player2=player2
    )

    await nats_bus.publish(GAME_ASSIGNED, assigned_dto)
    return assigned_dto


async def main():
    await nats_bus.connect()
    logger.info("Game Allocator active. Managing servers: %s", GAME_SERVERS)
    await nats_bus.subscribe(MATCHMAKING_MATCH_FOUND, handle_match_found_or_allocate, dto_class=GameAllocatePayload)
    await nats_bus.subscribe(GAME_ALLOCATE, handle_match_found_or_allocate, dto_class=GameAllocatePayload)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Game Allocator shut down.")
