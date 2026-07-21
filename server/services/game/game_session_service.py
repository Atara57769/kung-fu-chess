import asyncio
import logging
from typing import Dict
from server.network.models import GameRoom, ConnectedPlayer
from shared.protocol.protocol import serialize_snapshot, algebraic_to_move, algebraic_to_cell
from shared.protocol import MessageType
from shared.models.color import Color
from shared.constants import (
    ROOM_STATUS_ACTIVE, ROOM_STATUS_ENDED, COLOR_NAME_WHITE, COLOR_NAME_BLACK,
    FIELD_TYPE, FIELD_DATA
)
from shared.models.game_over_result import KEY_WINNER, KEY_MESSAGE, KEY_WHITE_RATING_CHANGE, KEY_BLACK_RATING_CHANGE

logger = logging.getLogger(__name__)

async def start_game_session(room: GameRoom, broadcast_room_state_fn, room_tick_loop_fn) -> None:
    """Transitions room status to active and starts tick task."""
    room.status = ROOM_STATUS_ACTIVE
    await broadcast_room_state_fn(room)
    room.tick_task = asyncio.create_task(room_tick_loop_fn(room))

async def broadcast_snapshot(room: GameRoom, pubsub) -> None:
    """Broadcasts a game snapshot directly to players and spectators via pubsub."""
    def make_snapshot_message(player: ConnectedPlayer) -> dict:
        snap = room.controller.get_snapshot(player_color=player.color)
        return {
            FIELD_TYPE: MessageType.SNAPSHOT,
            FIELD_DATA: serialize_snapshot(snap)
        }
    await pubsub.publish(room.room_id, make_snapshot_message)

async def send_snapshot_to(player: ConnectedPlayer, room: GameRoom, send_json_fn) -> None:
    """Sends current state snapshot to a specific player session."""
    snap = room.controller.get_snapshot(player_color=player.color)
    await send_json_fn(player.ws, {
        FIELD_TYPE: MessageType.SNAPSHOT,
        FIELD_DATA: serialize_snapshot(snap)
    })

async def process_game_click(player: ConnectedPlayer, cell_str: str, rooms: Dict[str, GameRoom], broadcast_snapshot_fn) -> None:
    """Validates client click coordinate and executes authorized click on player's controller."""
    room = rooms.get(player.room_id) if player.room_id else None
    if not room or room.status != ROOM_STATUS_ACTIVE:
        return
        
    if player.color not in (Color.WHITE, Color.BLACK):
        logger.warning(f"Unauthorized click attempt by spectator/non-player {player.username}")
        return

    try:
        cell = algebraic_to_cell(cell_str, room.board.height)
    except ValueError:
        return

    room.controller.click(cell, player_color=player.color)
    await broadcast_snapshot_fn(room)

async def process_game_jump(player: ConnectedPlayer, cell_str: str, rooms: Dict[str, GameRoom], broadcast_snapshot_fn) -> None:
    """Validates client jump coordinate and executes authorized jump on player's controller."""
    room = rooms.get(player.room_id) if player.room_id else None
    if not room or room.status != ROOM_STATUS_ACTIVE:
        return

    if player.color not in (Color.WHITE, Color.BLACK):
        logger.warning(f"Unauthorized jump attempt by spectator/non-player {player.username}")
        return

    try:
        cell = algebraic_to_cell(cell_str, room.board.height)
    except ValueError:
        return

    room.controller.jump(cell, player_color=player.color)
    await broadcast_snapshot_fn(room)

async def end_game(room: GameRoom, winner_color: str, db, elo_calc_fn, send_json_fn) -> None:
    """Resolves results, ELO updates, DB updates, and closes lobby tick loops."""
    room.status = ROOM_STATUS_ENDED
    if room.tick_task:
        room.tick_task.cancel()

    white_name = room.white_player.username if room.white_player else None
    black_name = room.black_player.username if room.black_player else None
    
    elo_w_str = ""
    elo_b_str = ""
    if room.white_player and room.black_player:
        r_w = room.white_player.rating
        r_b = room.black_player.rating
        
        outcome = 1.0 if winner_color == COLOR_NAME_WHITE else (0.0 if winner_color == COLOR_NAME_BLACK else 0.5)
        new_w, new_b = elo_calc_fn(r_w, r_b, outcome)
        
        db.update_user_rating(white_name, new_w)
        db.update_user_rating(black_name, new_b)
        
        room.white_player.rating = new_w
        room.black_player.rating = new_b
        
        elo_w_str = f" ({r_w} -> {new_w})"
        elo_b_str = f" ({r_b} -> {new_b})"
        
    payload = {
        FIELD_TYPE: MessageType.GAME_OVER,
        KEY_WINNER: winner_color,
        KEY_MESSAGE: f"Game Over! Winner: {winner_color.upper()}",
        KEY_WHITE_RATING_CHANGE: elo_w_str,
        KEY_BLACK_RATING_CHANGE: elo_b_str
    }

    clients = []
    if room.white_player: clients.append(room.white_player)
    if room.black_player: clients.append(room.black_player)
    clients.extend(room.spectators)
    
    for c in clients:
        await send_json_fn(c.ws, payload)

    logger.info(f"Game resolved in Room {room.room_id}. Winner={winner_color}")

