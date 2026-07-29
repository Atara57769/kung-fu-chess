import os
import uuid
import asyncio
import logging
from typing import Any, Optional
import redis.asyncio as aioredis

from shared.constants import DEFAULT_RATING, ResponseStatus
from shared.message_contracts.subjects import MATCHMAKING_REQUEST, MATCHMAKING_MATCH_FOUND, MATCHMAKING_TIMEOUT
from shared.message_contracts.contracts import (
    MatchFoundPayload, MatchmakingResponsePayload, MatchmakingRequestPayload, MatchmakingTimeoutPayload
)
from shared.message_contracts.nats_client import NatsBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Matchmaking Service: %(message)s")
logger = logging.getLogger("MatchmakingService")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
PLAYER_MATCH_TTL = int(os.getenv("PLAYER_MATCH_TTL", str(2 * 60 * 60)))   
QUEUE_PLAYER_TTL = int(os.getenv("QUEUE_PLAYER_TTL", "300"))              
ELO_TOLERANCE = int(os.getenv("ELO_TOLERANCE", "100"))
MATCH_POLL_INTERVAL = float(os.getenv("MATCH_POLL_INTERVAL", "1.0"))
MATCH_TIMEOUT_SECONDS = int(os.getenv("MATCH_TIMEOUT_SECONDS", "120"))    

QUEUE_KEY = "matchmaking_queue"           
PLAYER_KEY_PREFIX = "matchmaking_player"  

nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return redis_client

async def redis_enqueue(username: str, rating: int) -> None:
    """Add player to the Redis sorted set queue (score = rating)."""
    redis = await get_redis()
    pipe = redis.pipeline()
    pipe.zadd(QUEUE_KEY, {username: rating})
    pipe.hset(f"{PLAYER_KEY_PREFIX}:{username}", mapping={"username": username, "rating": str(rating)})
    pipe.expire(f"{PLAYER_KEY_PREFIX}:{username}", QUEUE_PLAYER_TTL)
    await pipe.execute()
    logger.info("Player '%s' (rating=%d) added to Redis matchmaking queue", username, rating)


async def redis_dequeue(username: str) -> None:
    """Remove player from the Redis sorted set queue."""
    redis = await get_redis()
    pipe = redis.pipeline()
    pipe.zrem(QUEUE_KEY, username)
    pipe.delete(f"{PLAYER_KEY_PREFIX}:{username}")
    await pipe.execute()
    logger.info("Player '%s' removed from Redis matchmaking queue", username)


async def redis_is_queued(username: str) -> bool:
    redis = await get_redis()
    return await redis.zscore(QUEUE_KEY, username) is not None


async def redis_find_opponent(username: str, rating: int) -> Optional[str]:
    """
    Find the closest opponent within ELO_TOLERANCE using the sorted set.
    Returns opponent username or None.
    """
    redis = await get_redis()
    lo, hi = rating - ELO_TOLERANCE, rating + ELO_TOLERANCE
    candidates: list = await redis.zrangebyscore(QUEUE_KEY, lo, hi)
    for candidate in candidates:
        if candidate != username:
            return candidate
    return None


async def redis_get_player_rating(username: str) -> int:
    redis = await get_redis()
    score = await redis.zscore(QUEUE_KEY, username)
    return int(score) if score is not None else DEFAULT_RATING

async def _on_pair_matched(username1: str, rating1: int, username2: str, rating2: int) -> None:
    match_id = f"match_{uuid.uuid4().hex[:8]}"
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    logger.info("Match found! %s (%d) vs %s (%d) -> Match '%s' (Room '%s')",
                username1, rating1, username2, rating2, match_id, room_id)

    match_dto = MatchFoundPayload(
        match_id=match_id,
        room_id=room_id,
        player1=username1,
        player2=username2
    )
    await nats_bus.publish(MATCHMAKING_MATCH_FOUND, match_dto)

    try:
        redis = await get_redis()
        pipe = redis.pipeline()
        pipe.set(f"player_match:{username1}", room_id, ex=PLAYER_MATCH_TTL)
        pipe.set(f"player_match:{username2}", room_id, ex=PLAYER_MATCH_TTL)
        await pipe.execute()
        logger.info("Saved player->match in Redis: %s->%s, %s->%s",
                    username1, room_id, username2, room_id)
    except Exception as e:
        logger.warning("Failed to save player->match in Redis: %s", e)



async def _run_match_loop(username: str, rating: int) -> None:
    """Polls Redis every MATCH_POLL_INTERVAL seconds looking for an ELO opponent.
    Gives up after MATCH_TIMEOUT_SECONDS and notifies the client.
    """
    elapsed = 0.0
    while await redis_is_queued(username):
        if elapsed >= MATCH_TIMEOUT_SECONDS:
            await redis_dequeue(username)
            logger.info("Matchmaking timed out for '%s' after %.0fs", username, elapsed)
            timeout_dto = MatchmakingTimeoutPayload(username=username)
            await nats_bus.publish(MATCHMAKING_TIMEOUT, timeout_dto)
            return

        opponent = await redis_find_opponent(username, rating)
        if opponent is not None:
            opp_rating = await redis_get_player_rating(opponent)
            redis = await get_redis()
            removed_self = await redis.zrem(QUEUE_KEY, username)
            removed_opp = await redis.zrem(QUEUE_KEY, opponent)
            if removed_self and removed_opp:
                await redis.delete(f"{PLAYER_KEY_PREFIX}:{username}", f"{PLAYER_KEY_PREFIX}:{opponent}")
                await _on_pair_matched(username, rating, opponent, opp_rating)
                return
            if not removed_self:
                return  
            if not removed_opp:
                await redis.zadd(QUEUE_KEY, {username: rating})
                logger.debug("Opponent '%s' already matched; retrying for '%s'", opponent, username)

        await asyncio.sleep(MATCH_POLL_INTERVAL)
        elapsed += MATCH_POLL_INTERVAL

    logger.debug("Match loop ended for '%s' (no longer in queue)", username)


async def handle_matchmaking_request(data: MatchmakingRequestPayload, reply_to: Optional[str]) -> Optional[MatchmakingResponsePayload]:
    action = data.action or "join"
    username = data.username
    rating = data.rating if data.rating is not None else DEFAULT_RATING

    if not username:
        return MatchmakingResponsePayload(status=ResponseStatus.FAILED.value, username="unknown")

    if action == "join":
        already_queued = await redis_is_queued(username)
        if not already_queued:
            await redis_enqueue(username, rating)
            asyncio.create_task(_run_match_loop(username, rating))
        return MatchmakingResponsePayload(status=ResponseStatus.QUEUED.value, username=username)

    elif action == "leave":
        await redis_dequeue(username)
        # Also clean up any stale player->match entry
        try:
            redis = await get_redis()
            await redis.delete(f"player_match:{username}")
        except Exception as e:
            logger.warning("Failed to remove player_match for '%s' from Redis: %s", username, e)
        return MatchmakingResponsePayload(status=ResponseStatus.REMOVED.value, username=username)

    return MatchmakingResponsePayload(status=ResponseStatus.FAILED.value, username=username)

async def main():
    await nats_bus.connect()
    logger.info("Matchmaking Service started. Subscribing to '%s'...", MATCHMAKING_REQUEST)
    await nats_bus.subscribe(MATCHMAKING_REQUEST, handle_matchmaking_request, dto_class=MatchmakingRequestPayload)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Matchmaking Service shut down.")
