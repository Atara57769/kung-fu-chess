import asyncio
import logging
from typing import Dict
from network.models import GameRoom, ConnectedPlayer
from network.protocol import serialize_snapshot, algebraic_to_move, algebraic_to_cell

logger = logging.getLogger(__name__)

async def start_game_session(room: GameRoom, broadcast_room_state_fn, room_tick_loop_fn) -> None:
    """Transitions room status to active and starts tick task."""
    room.status = "active"
    await broadcast_room_state_fn(room)
    room.tick_task = asyncio.create_task(room_tick_loop_fn(room))

async def broadcast_snapshot(room: GameRoom, send_json_fn) -> None:
    """Broadcasts current state snapshot to players and spectators."""
    snap = room.game_engine.snapshot(room.state)
    data = {
        "type": "snapshot",
        "data": serialize_snapshot(snap)
    }
    
    clients = []
    if room.white_player: clients.append(room.white_player)
    if room.black_player: clients.append(room.black_player)
    clients.extend(room.spectators)
    
    for c in clients:
        await send_json_fn(c.ws, data)

async def send_snapshot_to(player: ConnectedPlayer, room: GameRoom, send_json_fn) -> None:
    """Sends current state snapshot to a specific player session."""
    snap = room.game_engine.snapshot(room.state)
    await send_json_fn(player.ws, {
        "type": "snapshot",
        "data": serialize_snapshot(snap)
    })

async def process_game_move(player: ConnectedPlayer, move_str: str, rooms: Dict[str, GameRoom], broadcast_snapshot_fn) -> None:
    """Validates client command coordinates and executes authorized request_move."""
    room = rooms.get(player.room_id) if player.room_id else None
    if not room or room.status != "active":
        return
        
    try:
        from_cell, to_cell = algebraic_to_move(move_str, room.board.height)
    except ValueError:
        return

    piece = room.state.board.get_piece_at(from_cell)
    if piece is None or piece.color != player.color:
        logger.warning(f"Unauthorized move attempt by {player.username}: no owned piece at {from_cell}")
        return

    room.game_engine.request_move(room.state, from_cell, to_cell)
    await broadcast_snapshot_fn(room)

async def process_game_jump(player: ConnectedPlayer, cell_str: str, rooms: Dict[str, GameRoom], broadcast_snapshot_fn) -> None:
    """Validates client jump coordinate and executes authorized jump."""
    room = rooms.get(player.room_id) if player.room_id else None
    if not room or room.status != "active":
        return

    try:
        cell = algebraic_to_cell(cell_str, room.board.height)
    except ValueError:
        return

    piece = room.state.board.get_piece_at(cell)
    if piece is None or piece.color != player.color:
        logger.warning(f"Unauthorized jump attempt by {player.username}: no owned piece at {cell}")
        return

    room.game_engine.jump(room.state, cell)
    await broadcast_snapshot_fn(room)

async def end_game(room: GameRoom, winner_color: str, db, elo_calc_fn, send_json_fn) -> None:
    """Resolves results, ELO updates, DB updates, and closes lobby tick loops."""
    room.status = "ended"
    if room.tick_task:
        room.tick_task.cancel()

    white_name = room.white_player.username if room.white_player else None
    black_name = room.black_player.username if room.black_player else None
    
    elo_w_str = ""
    elo_b_str = ""
    if room.white_player and room.black_player:
        r_w = room.white_player.rating
        r_b = room.black_player.rating
        
        outcome = 1.0 if winner_color == "white" else (0.0 if winner_color == "black" else 0.5)
        new_w, new_b = elo_calc_fn(r_w, r_b, outcome)
        
        db.update_user_rating(white_name, new_w)
        db.update_user_rating(black_name, new_b)
        
        room.white_player.rating = new_w
        room.black_player.rating = new_b
        
        elo_w_str = f" ({r_w} -> {new_w})"
        elo_b_str = f" ({r_b} -> {new_b})"
        
    payload = {
        "type": "game_over",
        "winner": winner_color,
        "message": f"Game Over! Winner: {winner_color.upper()}",
        "white_rating_change": elo_w_str,
        "black_rating_change": elo_b_str
    }

    clients = []
    if room.white_player: clients.append(room.white_player)
    if room.black_player: clients.append(room.black_player)
    clients.extend(room.spectators)
    
    for c in clients:
        await send_json_fn(c.ws, payload)

    logger.info(f"Game resolved in Room {room.room_id}. Winner={winner_color}")
