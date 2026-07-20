import logging
import random
from typing import Dict, Optional
from network.models import ConnectedPlayer, GameRoom
from network.pubsub import make_subscriber_callback

logger = logging.getLogger(__name__)

async def create_custom_room(
    player: ConnectedPlayer,
    rooms: Dict[str, GameRoom],
    pubsub,
    send_json_fn,
    broadcast_room_state_fn
) -> None:
    """Creates custom lobby and seats creator as White."""
    room_id = str(random.randint(1000, 9999))
    while room_id in rooms:
        room_id = str(random.randint(1000, 9999))

    room = GameRoom(room_id)
    room.white_player = player
    player.room_id = room_id
    player.color = "w"
    
    rooms[room_id] = room
    pubsub.subscribe(room_id, player, make_subscriber_callback(player, send_json_fn))
    logger.info(f"Custom Room {room_id} created by {player.username}.")
    await broadcast_room_state_fn(room)

async def join_custom_room(
    player: ConnectedPlayer,
    room_id: str,
    rooms: Dict[str, GameRoom],
    pubsub,
    send_json_fn,
    broadcast_room_state_fn,
    start_game_callback,
    send_snapshot_to_fn
) -> None:
    """Joins custom lobby as Black (if empty) or Spectator."""
    room = rooms.get(room_id)
    if not room:
        await send_json_fn(player.ws, {"type": "error", "message": "Room not found."})
        return

    player.room_id = room_id
    
    if room.white_player and room.white_player.username == player.username and room.white_player != player:
        # Reconnecting White player
        room.white_player = player
        player.color = "w"
        if room.countdown_task:
            room.countdown_task.cancel()
            room.countdown_task = None
        pubsub.subscribe(room_id, player, make_subscriber_callback(player, send_json_fn))
        logger.info(f"Player {player.username} reconnected to Room {room_id} as White.")
        await broadcast_room_state_fn(room)
        await send_snapshot_to_fn(player, room)
    elif room.black_player and room.black_player.username == player.username and room.black_player != player:
        # Reconnecting Black player
        room.black_player = player
        player.color = "b"
        if room.countdown_task:
            room.countdown_task.cancel()
            room.countdown_task = None
        pubsub.subscribe(room_id, player, make_subscriber_callback(player, send_json_fn))
        logger.info(f"Player {player.username} reconnected to Room {room_id} as Black.")
        await broadcast_room_state_fn(room)
        await send_snapshot_to_fn(player, room)
    else:
        # Normal joining flow
        pubsub.subscribe(room_id, player, make_subscriber_callback(player, send_json_fn))
        if room.black_player is None and room.status == "waiting":
            room.black_player = player
            player.color = "b"
            logger.info(f"Player {player.username} joined Room {room_id} as Black.")
            await start_game_callback(room)
        else:
            room.spectators.append(player)
            player.color = None
            logger.info(f"Player {player.username} joined Room {room_id} as Spectator.")
            await broadcast_room_state_fn(room)
            if room.status == "active":
                await send_snapshot_to_fn(player, room)

async def handle_leave_room(
    player: ConnectedPlayer,
    rooms: Dict[str, GameRoom],
    pubsub,
    send_json_fn,
    broadcast_room_state_fn
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

    pubsub.unsubscribe(room_id, player)

    await broadcast_room_state_fn(room)
    await send_json_fn(player.ws, {"type": "room_state", "room_id": None})

async def broadcast_room_state(room: GameRoom, send_json_fn) -> None:
    """Sends current lobby rosters to all participants."""
    white_name = room.white_player.username if room.white_player else None
    black_name = room.black_player.username if room.black_player else None
    specs = [p.username for p in room.spectators if p.username]
    
    payload = {
        "type": "room_state",
        "room_id": room.room_id,
        "white": white_name,
        "black": black_name,
        "spectators": specs,
        "status": room.status
    }
    
    clients = []
    if room.white_player: clients.append(room.white_player)
    if room.black_player: clients.append(room.black_player)
    clients.extend(room.spectators)
    
    for c in clients:
        color_payload = dict(payload)
        color_payload["your_color"] = c.color
        await send_json_fn(c.ws, color_payload)
