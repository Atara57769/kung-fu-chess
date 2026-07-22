import asyncio
import logging
from typing import List, Dict, Optional
from server.network.models import ConnectedPlayer, GameRoom
from shared.constants import (
    DISCONNECT_COUNTDOWN, ROOM_STATUS_ACTIVE, COLOR_NAME_WHITE, COLOR_NAME_BLACK
)
from shared.protocol import CountdownMessage

logger = logging.getLogger(__name__)

async def handle_disconnect(player: ConnectedPlayer,
    matchmaking_queue: List[ConnectedPlayer],
    rooms: Dict[str, GameRoom],
    broadcast_room_state_fn,
    start_resign_countdown_fn
) -> None:
    """Starts countdown resignation timer if an active player disconnects."""
    if player in matchmaking_queue:
        matchmaking_queue.remove(player)

    if not player.room_id:
        return

    room_id = player.room_id
    room = rooms.get(room_id)
    if not room:
        return

    is_game_player = (room.white_player == player or room.black_player == player)
    
    if room.status == ROOM_STATUS_ACTIVE and is_game_player:
        opponent = room.black_player if room.white_player == player else room.white_player
        room.countdown_seconds = DISCONNECT_COUNTDOWN
        if room.countdown_task:
            room.countdown_task.cancel()
        room.countdown_task = asyncio.create_task(start_resign_countdown_fn(room, player, opponent))
    else:
        if room.white_player == player:
            room.white_player = None
        elif room.black_player == player:
            room.black_player = None
        elif player in room.spectators:
            room.spectators.remove(player)
            
        await broadcast_room_state_fn(room)

async def run_resign_countdown(
    room: GameRoom,
    disconnected: ConnectedPlayer,
    opponent: Optional[ConnectedPlayer],
    send_json_fn,
    end_game_fn
) -> None:
    """Waits up to 20 seconds; resigns disconnected player if they do not return."""
    try:
        while room.countdown_seconds > 0:
            if opponent:
                await send_json_fn(opponent.ws, CountdownMessage(
                    seconds=room.countdown_seconds,
                    message=f"Opponent disconnected. Autoresign in {room.countdown_seconds}s."
                ))
            await asyncio.sleep(1.0)
            room.countdown_seconds -= 1

        winner_color = COLOR_NAME_BLACK if room.white_player == disconnected else COLOR_NAME_WHITE
        logger.info(f"Countdown expired in Room {room.room_id}. Disconnected player {disconnected.username} resigned.")
        await end_game_fn(room, winner_color)
    except asyncio.CancelledError:
        logger.info(f"Resign countdown cancelled in Room {room.room_id} (player reconnected).")


