import asyncio
import logging
from typing import List
from server.network.models import ConnectedPlayer
from shared.protocol import MatchmakingStatusMessage
from shared.constants import (
    MATCHMAKING_STATUS_WAITING, MATCHMAKING_STATUS_IDLE
)

logger = logging.getLogger(__name__)

async def add_to_matchmaking(player: ConnectedPlayer, matchmaking_queue: List[ConnectedPlayer], send, pair_callback) -> None:
    """Adds player to matchmaking queue and attempts to pair them."""
    if player in matchmaking_queue:
        return
    matchmaking_queue.append(player)
    logger.info(f"Player {player.username} ({player.rating}) entered matchmaking queue.")
    await send(player.ws, MatchmakingStatusMessage(status=MATCHMAKING_STATUS_WAITING))
    
    asyncio.create_task(process_matchmaking_for_player(player, matchmaking_queue, send, pair_callback))

async def remove_from_matchmaking(player: ConnectedPlayer, matchmaking_queue: List[ConnectedPlayer], send) -> None:
    """Removes player from matchmaking queue."""
    if player in matchmaking_queue:
        matchmaking_queue.remove(player)
        logger.info(f"Player {player.username} left matchmaking queue.")
        await send(player.ws, MatchmakingStatusMessage(status=MATCHMAKING_STATUS_IDLE))


async def process_matchmaking_for_player(
    player: ConnectedPlayer,
    matchmaking_queue: List[ConnectedPlayer],
    send,
    pair_callback
) -> None:
    """Polls matchmaking queue seeking ELO partner until player leaves queue."""
    while player in matchmaking_queue:
        opponent = None
        for p in matchmaking_queue:
            if p != player and abs(p.rating - player.rating) <= 100:
                opponent = p
                break
        
        if opponent is not None:
            matchmaking_queue.remove(player)
            if opponent in matchmaking_queue:
                matchmaking_queue.remove(opponent)
            
            await pair_callback(player, opponent)
            return

        await asyncio.sleep(1.0)
