import asyncio
import json
import logging
import random
import time
import uuid
from typing import Dict, List, Optional
from shared.constants import (ROOM_STATUS_ACTIVE, COLOR_NAME_WHITE, COLOR_NAME_BLACK, MSG_UNAUTHORIZED, DISCONNECT_COUNTDOWN, MSG_DISCONNECT_COUNTDOWN)
from server.database.db_manager import DBManager
from shared.models.color import Color
from server.network.models import ConnectedPlayer, GameRoom
from server.services.game.game_session_service import GameSessionService
from server.services.matchmaking.room_service import RoomService, RoomJoinEvent
from server.services.auth import auth_service
from server.services.matchmaking import matchmaking_service
from shared.protocol import (MessageType, ErrorMessage, HeartbeatAckMessage, BaseMessage,parse_message, CountdownMessage)

logger = logging.getLogger(__name__)


class GameCoordinator:
    """Coordinates authentication, matchmaking, and authoritative game state routing."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db = DBManager(db_path) if db_path else DBManager()
        self.rooms: Dict[str, GameRoom] = {}
        self.matchmaking_queue: List[ConnectedPlayer] = []
        self.send = None
        self.game_session = GameSessionService(self.db)
        self.room_service = RoomService()
        self.message_handlers = {
            MessageType.MATCHMAKING: self._handle_matchmaking,
            MessageType.LEAVE_MATCHMAKING: self._handle_leave_matchmaking,
            MessageType.CREATE_ROOM: self._handle_create_room,
            MessageType.JOIN_ROOM: self._handle_join_room,
            MessageType.MOVE: self._handle_move,
            MessageType.JUMP: self._handle_jump,
            MessageType.LEAVE_ROOM: self._handle_leave_room,
            MessageType.GET_SNAPSHOT: self._handle_get_snapshot,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }

    def set_send(self, send) -> None:
        self.send = send
        self.room_service.send = send
        self.game_session.send = send

    async def dispatch_message(self, player: ConnectedPlayer, raw_msg: str) -> None:
        """Decodes JSON message and dispatches it to the correct action handler."""
        player.last_heartbeat = time.time()
        try:
            data = json.loads(raw_msg)
            msg = parse_message(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.warning("Received invalid or unparseable message.")
            return

        if msg.type == MessageType.AUTH:
            await auth_service.handle_auth(player, msg, self.db, self.send)
        elif not player.authenticated:
            await self.send(player.ws, ErrorMessage(message=MSG_UNAUTHORIZED))
        else:
            await self._handle_authenticated_message(player, msg)

    async def _handle_authenticated_message(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        """Dispatches authenticated client message to its matching handler."""
        handler = self.message_handlers.get(msg.type)
        if handler:
            await handler(player, msg)
        else:
            logger.warning(f"Received unhandled message type: {msg.type}")

    async def _handle_matchmaking(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await matchmaking_service.add_to_matchmaking(
            player, self.matchmaking_queue, self.send, self._start_matched_game
        )

    async def _handle_leave_matchmaking(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await matchmaking_service.remove_from_matchmaking(
            player, self.matchmaking_queue, self.send
        )

    async def _handle_create_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        custom_id = getattr(msg, "room_id", None)
        await self.room_service.create_room(player, self.rooms, custom_id)

    async def _handle_join_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        room_id = getattr(msg, "room_id", "")
        event, room = await self.room_service.join_room(
            player, room_id, self.rooms)
        if event == RoomJoinEvent.GAME_CAN_START:
            await self.game_session.start_game(room)
            await self.room_service.broadcast_room_state(room)
        elif event in (RoomJoinEvent.RECONNECTED, RoomJoinEvent.SPECTATOR_ACTIVE):
            await self.game_session.send_snapshot(player, room)

    async def _handle_move(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await self.game_session.process_move(
            player, getattr(msg, "data", ""), self.rooms)

    async def _handle_jump(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await self.game_session.process_jump(
            player, getattr(msg, "data", ""), self.rooms)

    async def _handle_leave_room(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await self.room_service.leave_room(player, self.rooms)

    async def _handle_get_snapshot(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        room = self.rooms.get(player.room_id) if player.room_id else None
        if room:
            await self.game_session.send_snapshot(player, room)

    async def _handle_heartbeat(self, player: ConnectedPlayer, msg: BaseMessage) -> None:
        await self.send(player.ws, HeartbeatAckMessage())

    async def _start_matched_game(self, p1: ConnectedPlayer, p2: ConnectedPlayer) -> None:
        """Pairs two matchmaking players into a new room and starts game."""
        room_id = uuid.uuid4().hex[:8]
        white, black = (p1, p2) if random.choice([True, False]) else (p2, p1)
        room = self.room_service.build_room(room_id, self.rooms, white=white, black=black)
        logger.info(f"Matched game started in Room {room_id}: White={white.username}, Black={black.username}.")
        await self.game_session.start_game(room)
        await self.room_service.broadcast_room_state(room)

    async def handle_disconnect(self, player: ConnectedPlayer) -> None:
        """Removes player from queue/room and starts auto-resign countdown if mid-game."""
        if player in self.matchmaking_queue:
            self.matchmaking_queue.remove(player)

        if not player.room_id:
            return

        room = self.rooms.get(player.room_id)
        if not room:
            return

        is_game_player = (room.white_player == player or room.black_player == player)

        if room.status == ROOM_STATUS_ACTIVE and is_game_player:
            opponent = room.black_player if room.white_player == player else room.white_player
            room.countdown_seconds = DISCONNECT_COUNTDOWN
            if room.countdown_task:
                room.countdown_task.cancel()
            room.countdown_task = asyncio.create_task(
                self._run_resign_countdown(room, player, opponent)
            )
        else:
            if room.white_player == player:
                room.white_player = None
            elif room.black_player == player:
                room.black_player = None
            elif player in room.spectators:
                room.spectators.remove(player)
            await self.room_service.broadcast_room_state(room)

    async def _run_resign_countdown(
        self,
        room: GameRoom,
        disconnected: ConnectedPlayer,
        opponent: Optional[ConnectedPlayer]
    ) -> None:
        """Waits up to DISCONNECT_COUNTDOWN seconds; auto-resigns if player doesn't return."""
        try:
            while room.countdown_seconds > 0:
                if opponent and self.send:
                    await self.send(opponent.ws, CountdownMessage(
                        seconds=room.countdown_seconds,
                        message=MSG_DISCONNECT_COUNTDOWN.format(room.countdown_seconds)
                    ))
                await asyncio.sleep(1.0)
                room.countdown_seconds -= 1

            winner_color = COLOR_NAME_BLACK if room.white_player == disconnected else COLOR_NAME_WHITE
            logger.info(f"Countdown expired in Room {room.room_id}. {disconnected.username} resigned.")
            await self.game_session.end_game(room, winner_color)
        except asyncio.CancelledError:
            logger.info(f"Resign countdown cancelled in Room {room.room_id} (player reconnected).")
