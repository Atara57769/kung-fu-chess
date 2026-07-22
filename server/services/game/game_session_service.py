import asyncio
import logging
from typing import Dict
from server.network.models import GameRoom, ConnectedPlayer
from shared.protocol.protocol import serialize_snapshot, algebraic_to_move, algebraic_to_cell
from shared.protocol import SnapshotMessage, GameOverMessage
from shared.models.color import Color
from client.ui.ui_config import TIME_STEP_MS
from shared.constants import (
    ROOM_STATUS_ACTIVE, ROOM_STATUS_ENDED, COLOR_NAME_WHITE, COLOR_NAME_BLACK,
    GAME_RESULT_DRAW
)

ATTR_WINNER = "winner"
PIECE_KIND_KING = "K"
RATING_CHANGE_FORMAT = " ({} -> {})"
GAME_OVER_MESSAGE_FORMAT = "Game Over! Winner: {}"

logger = logging.getLogger(__name__)

class GameSessionService:
    """Manages authoritative game state: ticking, moves, snapshots, and end-game resolution."""

    def __init__(self, db) -> None:
        self.db = db

    async def start_game(self, room: GameRoom, send_json_fn) -> None:
        """Transitions room status to active and starts the tick task."""
        room.status = ROOM_STATUS_ACTIVE
        room.tick_task = asyncio.create_task(self._tick_loop(room, send_json_fn))

    async def _tick_loop(self, room: GameRoom, send_json_fn) -> None:
        """Authoritative real-time progression ticking game state."""
        tick_interval = TIME_STEP_MS / 1000.0
        try:
            while room.status == ROOM_STATUS_ACTIVE:
                await asyncio.sleep(tick_interval)
                room.controller.wait(TIME_STEP_MS)

                if room.state.game_over:
                    winner_token = room.state.winner if hasattr(room.state, ATTR_WINNER) else None
                    if not winner_token:
                        has_w_king = False
                        has_b_king = False
                        for row in room.state.board.grid:
                            for p in row:
                                if p is not None and p.kind == PIECE_KIND_KING:
                                    if p.color == Color.WHITE: has_w_king = True
                                    elif p.color == Color.BLACK: has_b_king = True
                        if has_w_king and not has_b_king:
                            winner_token = Color.WHITE
                        elif has_b_king and not has_w_king:
                            winner_token = Color.BLACK

                    winner_color = (
                        COLOR_NAME_WHITE if winner_token == Color.WHITE
                        else (COLOR_NAME_BLACK if winner_token == Color.BLACK else GAME_RESULT_DRAW)
                    )
                    await self.end_game(room, winner_color, send_json_fn)
                    break

                await self.broadcast_snapshot(room, send_json_fn)
        except asyncio.CancelledError:
            pass

    async def broadcast_snapshot(self, room: GameRoom, send_json_fn) -> None:
        """Broadcasts a game snapshot directly to players and spectators."""
        clients = []
        if room.white_player: clients.append(room.white_player)
        if room.black_player: clients.append(room.black_player)
        clients.extend(room.spectators)
        for c in clients:
            snap = room.controller.get_snapshot(player_color=c.color)
            await send_json_fn(c.ws, SnapshotMessage(data=serialize_snapshot(snap)))

    async def send_snapshot(self, player: ConnectedPlayer, room: GameRoom, send_json_fn) -> None:
        """Sends current state snapshot to a specific player."""
        snap = room.controller.get_snapshot(player_color=player.color)
        await send_json_fn(player.ws, SnapshotMessage(data=serialize_snapshot(snap)))

    async def process_move(self, player: ConnectedPlayer, move_str: str, rooms: Dict[str, GameRoom], send_json_fn) -> None:
        """Validates and executes an authorized move on the player's controller."""
        room = rooms.get(player.room_id) if player.room_id else None
        if not room or room.status != ROOM_STATUS_ACTIVE:
            return
        if player.color not in (Color.WHITE, Color.BLACK):
            logger.warning(f"Unauthorized move attempt by spectator/non-player {player.username}")
            return
        try:
            from_cell, to_cell = algebraic_to_move(move_str, room.board.height)
        except ValueError:
            return
        room.controller.move(from_cell, to_cell, player_color=player.color)
        await self.broadcast_snapshot(room, send_json_fn)

    async def process_jump(self, player: ConnectedPlayer, cell_str: str, rooms: Dict[str, GameRoom], send_json_fn) -> None:
        """Validates and executes an authorized jump on the player's controller."""
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
        await self.broadcast_snapshot(room, send_json_fn)

    async def end_game(self, room: GameRoom, winner_color: str, send_json_fn) -> None:
        """Resolves results, ELO updates, DB writes, and stops the tick loop."""
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
            outcome = (
                1.0 if winner_color == COLOR_NAME_WHITE
                else (0.0 if winner_color == COLOR_NAME_BLACK else 0.5)
            )
            new_w, new_b = self._calculate_elo(r_w, r_b, outcome)
            self.db.update_user_rating(white_name, new_w)
            self.db.update_user_rating(black_name, new_b)
            room.white_player.rating = new_w
            room.black_player.rating = new_b
            elo_w_str = RATING_CHANGE_FORMAT.format(r_w, new_w)
            elo_b_str = RATING_CHANGE_FORMAT.format(r_b, new_b)

        payload = GameOverMessage(
            winner=winner_color,
            message=GAME_OVER_MESSAGE_FORMAT.format(winner_color.upper()),
            white_rating_change=elo_w_str,
            black_rating_change=elo_b_str
        )
        clients = []
        if room.white_player: clients.append(room.white_player)
        if room.black_player: clients.append(room.black_player)
        clients.extend(room.spectators)
        for c in clients:
            await send_json_fn(c.ws, payload)
        logger.info(f"Game resolved in Room {room.room_id}. Winner={winner_color}")

    @staticmethod
    def _calculate_elo(rating_w: int, rating_b: int, outcome: float) -> tuple[int, int]:
        """Standard ELO rating shift formula.
        outcome: 1.0 = White win, 0.0 = Black win, 0.5 = Draw.
        """
        k = 32
        expected_w = 1.0 / (1.0 + 10 ** ((rating_b - rating_w) / 400.0))
        expected_b = 1.0 - expected_w
        new_w = int(rating_w + k * (outcome - expected_w))
        new_b = int(rating_b + k * ((1.0 - outcome) - expected_b))
        return new_w, new_b
