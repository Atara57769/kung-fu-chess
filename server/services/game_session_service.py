import asyncio
import logging
from typing import Dict, Optional, Callable
from server.network.models import GameRoom, ConnectedPlayer
from server.database.base_db_manager import BaseDBManager
from shared.protocol.protocol import serialize_snapshot
from shared.protocol import SnapshotMessage, GameOverMessage, MoveMessage, JumpMessage

from shared.models.color import Color
from shared.constants import (
    ROOM_STATUS_ACTIVE, ROOM_STATUS_ENDED, COLOR_NAME_WHITE, COLOR_NAME_BLACK,
    GAME_RESULT_DRAW, TICK_STEP_MS, ELO_K_FACTOR, ELO_SCALE_FACTOR, ELO_BASE,
    ELO_OUTCOME_WIN, ELO_OUTCOME_LOSS, ELO_OUTCOME_DRAW
)

logger = logging.getLogger(__name__)

class GameSessionService:
    """Manages authoritative game state: ticking, moves, snapshots, and end-game resolution."""

    def __init__(self, db: BaseDBManager, send: Optional[Callable] = None) -> None:
        self.db = db
        self.send = send

    async def start_game(self, room: GameRoom) -> None:
        """Transitions room status to active and starts the tick task."""
        room.status = ROOM_STATUS_ACTIVE
        room.tick_task = asyncio.create_task(self._tick_loop(room))

    async def _tick_loop(self, room: GameRoom) -> None:
        """Authoritative real-time progression ticking game state."""
        tick_interval = TICK_STEP_MS / 1000.0
        try:
            while room.status == ROOM_STATUS_ACTIVE:
                await asyncio.sleep(tick_interval)
                room.controller.wait(TICK_STEP_MS)

                if room.state.game_over:
                    winner_token = room.state.winner
                    winner_color = (
                        COLOR_NAME_WHITE if winner_token == Color.WHITE
                        else (COLOR_NAME_BLACK if winner_token == Color.BLACK else GAME_RESULT_DRAW)
                    )
                    await self.end_game(room, winner_color)
                    break

                await self.broadcast_snapshot(room)
        except asyncio.CancelledError:
            pass

    async def broadcast_snapshot(self, room: GameRoom) -> None:
        """Broadcasts a game snapshot directly to players and spectators."""
        if not self.send:
            return
        clients = []
        if room.white_player: clients.append(room.white_player)
        if room.black_player: clients.append(room.black_player)
        clients.extend(room.spectators)
        for c in clients:
            snap = room.controller.get_snapshot(player_color=c.color)
            await self.send(c.ws, SnapshotMessage(data=serialize_snapshot(snap)))

    async def send_snapshot(self, player: ConnectedPlayer, room: GameRoom) -> None:
        """Sends current state snapshot to a specific player."""
        if not self.send:
            return
        snap = room.controller.get_snapshot(player_color=player.color)
        await self.send(player.ws, SnapshotMessage(data=serialize_snapshot(snap)))

    async def process_move(self, player: ConnectedPlayer, msg: MoveMessage, rooms: Dict[str, GameRoom]) -> None:
        """Validates and executes an authorized move on the player's controller."""
        room = rooms.get(player.room_id) if player.room_id else None
        if not room or room.status != ROOM_STATUS_ACTIVE:
            return
        if player.color not in (Color.WHITE, Color.BLACK):
            logger.warning(f"Unauthorized move attempt by spectator/non-player {player.username}")
            return
        if not msg.from_cell or not msg.to_cell:
            return
        room.controller.move(msg.from_cell, msg.to_cell, player_color=player.color)
        await self.broadcast_snapshot(room)

    async def process_jump(self, player: ConnectedPlayer, msg: JumpMessage, rooms: Dict[str, GameRoom]) -> None:
        """Validates and executes an authorized jump on the player's controller."""
        room = rooms.get(player.room_id) if player.room_id else None
        if not room or room.status != ROOM_STATUS_ACTIVE:
            return
        if player.color not in (Color.WHITE, Color.BLACK):
            logger.warning(f"Unauthorized jump attempt by spectator/non-player {player.username}")
            return
        if not msg.cell:
            return
        room.controller.jump(msg.cell, player_color=player.color)
        await self.broadcast_snapshot(room)


    async def end_game(self, room: GameRoom, winner_color: str) -> None:
        """Resolves results, ELO updates, DB writes, and stops the tick loop."""
        room.status = ROOM_STATUS_ENDED
        if room.tick_task:
            room.tick_task.cancel()

        white_name = room.white_player.username if room.white_player else None
        black_name = room.black_player.username if room.black_player else None

        new_w = None
        new_b = None
        if room.white_player and room.black_player:
            r_w = room.white_player.rating
            r_b = room.black_player.rating
            outcome = (
                ELO_OUTCOME_WIN if winner_color == COLOR_NAME_WHITE
                else (ELO_OUTCOME_LOSS if winner_color == COLOR_NAME_BLACK else ELO_OUTCOME_DRAW)
            )
            new_w, new_b = self._calculate_elo(r_w, r_b, outcome)
            self.db.update_user_rating(white_name, new_w)
            self.db.update_user_rating(black_name, new_b)
            room.white_player.rating = new_w
            room.black_player.rating = new_b

        payload = GameOverMessage(
            winner=winner_color,
            white_rating=new_w,
            black_rating=new_b
        )
        if self.send:
            clients = []
            if room.white_player: clients.append(room.white_player)
            if room.black_player: clients.append(room.black_player)
            clients.extend(room.spectators)
            for c in clients:
                await self.send(c.ws, payload)
        logger.info(f"Game resolved in Room {room.room_id}. Winner={winner_color}")

    @staticmethod
    def _calculate_elo(rating_w: int, rating_b: int, outcome: float) -> tuple[int, int]:
        """Standard ELO rating shift formula using configured Elo constants."""
        expected_w = ELO_OUTCOME_WIN / (ELO_OUTCOME_WIN + ELO_BASE ** ((rating_b - rating_w) / ELO_SCALE_FACTOR))
        expected_b = ELO_OUTCOME_WIN - expected_w
        new_w = int(rating_w + ELO_K_FACTOR * (outcome - expected_w))
        new_b = int(rating_b + ELO_K_FACTOR * ((ELO_OUTCOME_WIN - outcome) - expected_b))
        return new_w, new_b
