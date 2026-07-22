import logging
import random
from typing import Dict, Optional
from server.network.models import ConnectedPlayer, GameRoom
from shared.protocol import ErrorMessage, RoomStateMessage
from shared.models.color import Color
from shared.constants import (
    ROOM_STATUS_WAITING, ROOM_STATUS_ACTIVE,
    MSG_ROOM_ALREADY_EXISTS, MSG_ROOM_NOT_FOUND
)

logger = logging.getLogger(__name__)

async def create_custom_room(
    player: ConnectedPlayer,
    rooms: Dict[str, GameRoom],
    send_json_fn,
    room_id: Optional[str] = None
) -> None:
    """Creates custom lobby and seats creator as White."""
    if not room_id:
        room_id = str(random.randint(1000, 9999))
        while room_id in rooms:
            room_id = str(random.randint(1000, 9999))
    else:
        if room_id in rooms:
            await send_json_fn(player.ws, ErrorMessage(message=MSG_ROOM_ALREADY_EXISTS))
            return

    room = GameRoom(room_id)
    room.white_player = player
    player.room_id = room_id
    player.color = Color.WHITE
    
    rooms[room_id] = room
    logger.info(f"Custom Room {room_id} created by {player.username}.")
    await broadcast_room_state(room, send_json_fn)

async def join_custom_room(
    player: ConnectedPlayer,
    room_id: str,
    rooms: Dict[str, GameRoom],
    send_json_fn,
    db
) -> None:
    """Joins custom lobby as Black (if empty) or Spectator."""
    from server.services.game import game_session_service

    room = rooms.get(room_id)
    if not room:
        await send_json_fn(player.ws, ErrorMessage(message=MSG_ROOM_NOT_FOUND))
        return

    player.room_id = room_id
    
    if room.white_player and room.white_player.username == player.username and room.white_player != player:
        room.white_player = player
        player.color = Color.WHITE
        if room.countdown_task:
            room.countdown_task.cancel()
            room.countdown_task = None
        logger.info(f"Player {player.username} reconnected to Room {room_id} as White.")
        await broadcast_room_state(room, send_json_fn)
        await game_session_service.send_snapshot_to(player, room, send_json_fn)
    elif room.black_player and room.black_player.username == player.username and room.black_player != player:
        room.black_player = player
        player.color = Color.BLACK
        if room.countdown_task:
            room.countdown_task.cancel()
            room.countdown_task = None
        logger.info(f"Player {player.username} reconnected to Room {room_id} as Black.")
        await broadcast_room_state(room, send_json_fn)
        await game_session_service.send_snapshot_to(player, room, send_json_fn)
    else:
        if room.black_player is None and room.status == ROOM_STATUS_WAITING:
            room.black_player = player
            player.color = Color.BLACK
            logger.info(f"Player {player.username} joined Room {room_id} as Black.")
            await game_session_service.start_game_session(room, db, send_json_fn)
        else:
            room.spectators.append(player)
            player.color = None
            logger.info(f"Player {player.username} joined Room {room_id} as Spectator.")
            await broadcast_room_state(room, send_json_fn)
            if room.status == ROOM_STATUS_ACTIVE:
                await game_session_service.send_snapshot_to(player, room, send_json_fn)

async def handle_leave_room(
    player: ConnectedPlayer,
    rooms: Dict[str, GameRoom],
    send_json_fn
) -> None:
    """Removes a player from their current lobby session."""
    if not player.room_id:
        return
    room_id = player.room_id
    room = rooms.get(room_id)
    if not room:
        return

    if room.white_player == player:
        room.white_player = None
    elif room.black_player == player:
        room.black_player = None
    elif player in room.spectators:
        room.spectators.remove(player)

    player.room_id = None
    player.color = None

    await broadcast_room_state(room, send_json_fn)
    await send_json_fn(player.ws, RoomStateMessage(room_id=None))

async def broadcast_room_state(room: GameRoom, send_json_fn) -> None:
    """Sends current lobby rosters to all participants."""
    white_name = room.white_player.username if room.white_player else None
    black_name = room.black_player.username if room.black_player else None
    specs = [p.username for p in room.spectators if p.username]
    
    clients = []
    if room.white_player: clients.append(room.white_player)
    if room.black_player: clients.append(room.black_player)
    clients.extend(room.spectators)
    
    for c in clients:
        msg = RoomStateMessage(
            room_id=room.room_id,
            white=white_name,
            black=black_name,
            spectators=specs,
            status=room.status,
            your_color=c.color
        )
        await send_json_fn(c.ws, msg)


