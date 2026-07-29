import asyncio
import logging
from typing import List
from server.network.models import ConnectedPlayer
from shared.protocol import MatchmakingStatusMessage
from shared.constants import (
    MATCHMAKING_STATUS_WAITING, MATCHMAKING_STATUS_IDLE
)
from server.services.server_event_bus import ServerEventType, ServerEventBus
from typing import List, Optional

logger = logging.getLogger(__name__)

async def add_to_matchmaking(player: ConnectedPlayer, matchmaking_queue: List[ConnectedPlayer], pair_callback=None, event_bus: Optional[ServerEventBus] = None) -> None:
    """Adds player to matchmaking queue and attempts to pair them."""
    if player in matchmaking_queue:
        return
    matchmaking_queue.append(player)
    logger.info(f"Player {player.username} ({player.rating}) entered matchmaking queue.")
    status_msg = MatchmakingStatusMessage(status=MATCHMAKING_STATUS_WAITING)
    if event_bus:
        await event_bus.publish(ServerEventType.MATCHMAKING_STATUS, target=player, data=status_msg)
    
    asyncio.create_task(process_matchmaking_for_player(player, matchmaking_queue, pair_callback, event_bus))

async def remove_from_matchmaking(player: ConnectedPlayer, matchmaking_queue: List[ConnectedPlayer], event_bus: Optional[ServerEventBus] = None) -> None:
    """Removes player from matchmaking queue."""
    if player in matchmaking_queue:
        matchmaking_queue.remove(player)
        logger.info(f"Player {player.username} left matchmaking queue.")
        status_msg = MatchmakingStatusMessage(status=MATCHMAKING_STATUS_IDLE)
        if event_bus:
            await event_bus.publish(ServerEventType.MATCHMAKING_STATUS, target=player, data=status_msg)


async def process_matchmaking_for_player(
    player: ConnectedPlayer,
    matchmaking_queue: List[ConnectedPlayer],
    pair_callback=None,
    event_bus: Optional[ServerEventBus] = None
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
