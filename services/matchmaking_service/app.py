import os
import uuid
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

from shared.constants import DEFAULT_RATING, ResponseStatus
from shared.message_contracts.subjects import MATCHMAKING_REQUEST, MATCHMAKING_MATCH_FOUND
from shared.message_contracts.contracts import MatchFoundPayload, MatchmakingResponsePayload, MatchmakingRequestPayload
from shared.message_contracts.nats_client import NatsBus
from server.network.models import ConnectedPlayer
from server.services.matchmaking_service import add_to_matchmaking, remove_from_matchmaking

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Matchmaking Service: %(message)s")
logger = logging.getLogger("MatchmakingService")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
nats_bus = NatsBus(url=NATS_URL)

matchmaking_queue: List[ConnectedPlayer] = []
player_registry: Dict[str, ConnectedPlayer] = {}

async def _on_pair_matched(p1: ConnectedPlayer, p2: ConnectedPlayer) -> None:
    match_id = f"match_{uuid.uuid4().hex[:8]}"
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    logger.info("Match found! %s (%d) vs %s (%d) -> Match '%s' (Room '%s')",
                p1.username, p1.rating, p2.username, p2.rating, match_id, room_id)

    match_dto = MatchFoundPayload(
        match_id=match_id,
        room_id=room_id,
        player1=p1.username,
        player2=p2.username
    )
    await nats_bus.publish(MATCHMAKING_MATCH_FOUND, match_dto)


async def _noop_send(ws: Any, msg: Any) -> None:
    pass


async def handle_matchmaking_request(data: MatchmakingRequestPayload, reply_to: Optional[str]) -> Optional[MatchmakingResponsePayload]:
    action = data.action or "join"
    username = data.username
    rating = data.rating if data.rating is not None else DEFAULT_RATING

    if not username:
        return MatchmakingResponsePayload(status=ResponseStatus.FAILED.value, username="unknown")

    if action == "join":
        player = player_registry.get(username)
        if not player:
            player = ConnectedPlayer(ws=None, ip_address="remote")
            player.username = username
            player.rating = rating
            player.authenticated = True
            player_registry[username] = player

        await add_to_matchmaking(player, matchmaking_queue, _noop_send, _on_pair_matched)
        return MatchmakingResponsePayload(status=ResponseStatus.QUEUED.value, username=username)

    elif action == "leave":
        player = player_registry.get(username)
        if player:
            await remove_from_matchmaking(player, matchmaking_queue, _noop_send)
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
