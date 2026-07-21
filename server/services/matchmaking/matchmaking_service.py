import asyncio
import logging
import time
from typing import List
from server.network.models import ConnectedPlayer

logger = logging.getLogger(__name__)

async def add_to_matchmaking( player: ConnectedPlayer, matchmaking_queue: List[ConnectedPlayer], send_json_fn, pair_callback) -> None:
    """Adds player to matchmaking queue and attempts to pair them."""
    if player in matchmaking_queue:
        return
    matchmaking_queue.append(player)
    logger.info(f"Player {player.username} ({player.rating}) entered matchmaking queue.")
    await send_json_fn(player.ws, {"type": "matchmaking_status", "status": "waiting"})
    
    asyncio.create_task(process_matchmaking_for_player(player, matchmaking_queue, send_json_fn, pair_callback))

async def remove_from_matchmaking(player: ConnectedPlayer,matchmaking_queue: List[ConnectedPlayer],send_json_fn) -> None:
    """Removes player from matchmaking queue."""
    if player in matchmaking_queue:
        matchmaking_queue.remove(player)
        logger.info(f"Player {player.username} left matchmaking queue.")
        await send_json_fn(player.ws, {"type": "matchmaking_status", "status": "idle"})

async def process_matchmaking_for_player(
    player: ConnectedPlayer,
    matchmaking_queue: List[ConnectedPlayer],
    send_json_fn,
    pair_callback
) -> None:
    """Polls matchmaking queue for up to 60 seconds seeking ELO partner."""
    start_time = time.time()
    while player in matchmaking_queue:
        if time.time() - start_time >= 60.0:
            if player in matchmaking_queue:
                matchmaking_queue.remove(player)
                await send_json_fn(player.ws, {"type": "matchmaking_status", "status": "timeout"})
                logger.info(f"Matchmaking timeout for player {player.username}.")
            return

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
