import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis

from shared.constants import ResponseStatus, ROOM_STATUS_ACTIVE, MSG_ROOM_NOT_FOUND
from shared.protocol import (
    MessageType,
    deserialize_message,
    serialize_message,
    RoomStateMessage,
    ErrorMessage
)
from shared.models.color import Color
from shared.message_contracts.subjects import (
    GAME_ASSIGNED, GAME_COMMAND, GAME_STATE, GAME_FINISHED, GAME_EVENTS, ROOM_JOIN, ROOM_LEAVE
)
from shared.message_contracts.contracts import (
    GameStatePayload, GameAssignedPayload, GameFinishedPayload, GameCommandPayload,
    RoomJoinPayload, RoomLeavePayload
)
from shared.message_contracts.nats_client import NatsBus
from server.network.models import GameRoom, ConnectedPlayer
from server.database.sqlite_db_manager import SQLiteDBManager
from server.database.postgres_db_manager import PostgresDBManager
from server.services.game_coordinator import GameCoordinator
from server.services.room_service import RoomJoinEvent

SERVER_ID = os.getenv("SERVER_ID", "game_server_1")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [%(levelname)s] GameServer[{SERVER_ID}]: %(message)s")
logger = logging.getLogger(f"GameServer[{SERVER_ID}]")

db_manager = PostgresDBManager()
nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return redis_client


async def delete_redis_route(room_id: str) -> None:
    try:
        redis = await get_redis()
        await redis.hdel("room_routes", room_id)
        logger.info("Removed route for room '%s' from Redis", room_id)
    except Exception as e:
        logger.warning("Failed to remove room_routes for %s in Redis: %s", room_id, e)


class NatsGameCoordinator(GameCoordinator):
    """Subclass of GameCoordinator adapted for NATS event bus communication."""

    def __init__(self, db=db_manager):
        super().__init__(db=db)
        self.set_send(self._nats_send)
        self.on_room_cleanup = delete_redis_route

    async def _nats_send(self, ws_target, message_obj: Any) -> None:
        """Publishes game state snapshots and events to NATS subject using GameStatePayload DTO."""
        raw = serialize_message(message_obj) if not isinstance(message_obj, str) else message_obj
        state_content = json.loads(raw) if isinstance(raw, str) and raw.startswith("{") else raw

        # ws_target is None for remote players (distributed mode).
        # Extract target info from the player object if available, otherwise from the message itself.
        target_user = None
        room_id = None

        if ws_target is not None:
            target_user = getattr(ws_target, "username", None)
            room_id = getattr(ws_target, "room_id", None)

        # Fallback: extract from the message object fields directly
        if target_user is None:
            target_user = getattr(message_obj, "target_username", None) or state_content.get("target_username")
        if room_id is None:
            room_id = getattr(message_obj, "room_id", None) or state_content.get("room_id")

        # For RoomStateMessage sent via broadcast_room_state, ws_target is c.ws (None),
        # but the RoomStateMessage itself has room_id. We need the target username from
        # the per-player msg (each client gets their own colored msg), but it's not stored
        # in RoomStateMessage. So we broadcast to all sockets subscribed to this room instead.
        payload_dto = GameStatePayload(
            room_id=room_id,
            state=state_content,
            target_username=target_user
        )
        await nats_bus.publish(GAME_STATE, payload_dto)



coordinator = NatsGameCoordinator(db=db_manager)


async def handle_game_assigned(data: GameAssignedPayload, reply_to: Optional[str]) -> Optional[Dict[str, Any]]:
    target_server = data.game_server_id
    if target_server and target_server != SERVER_ID:
        return None

    room_id = data.room_id
    player1 = data.player1
    player2 = data.player2

    if not room_id or not player1:
        return None

    logger.info("Assigning game session for room '%s' (%s vs %s)", room_id, player1, player2)

    p1_obj = ConnectedPlayer(ws=None, ip_address="remote")
    p1_obj.username = player1
    p1_obj.authenticated = True

    p2_obj = None
    if player2:
        p2_obj = ConnectedPlayer(ws=None, ip_address="remote")
        p2_obj.username = player2
        p2_obj.authenticated = True

    room = coordinator.rooms.get(room_id)
    if not room:
        room = coordinator.room_service.build_room(room_id, coordinator.rooms, white=p1_obj, black=p2_obj)
    else:
        room.white_player = p1_obj
        if p2_obj:
            room.black_player = p2_obj

    try:
        redis = await get_redis()
        await redis.hset("room_routes", room_id, SERVER_ID)
    except Exception as e:
        logger.warning("Failed to write room_routes to Redis: %s", e)

    if player2:
        await coordinator.game_session.start_game(room)
        logger.info("Game engine loop active for room '%s'", room_id)

    await coordinator.room_service.broadcast_room_state(room)

    return {"status": ResponseStatus.STARTED.value if player2 else ResponseStatus.CREATED.value, "room_id": room_id, "server_id": SERVER_ID}


async def handle_game_command(data: GameCommandPayload, reply_to: Optional[str]) -> Optional[Dict[str, Any]]:
    target_server = getattr(data, "target_server", None)
    if target_server and target_server != SERVER_ID:
        return None

    room_id = data.room_id
    username = data.username
    cmd_data = data.data or {}
    msg_type = cmd_data.get("type") if isinstance(cmd_data, dict) else None
    if not msg_type and isinstance(cmd_data, str):
        msg_type = cmd_data

    if msg_type in (MessageType.HEARTBEAT, MessageType.HEARTBEAT.value, "heartbeat"):
        return None

    if msg_type in (MessageType.CREATE_ROOM, MessageType.CREATE_ROOM.value, "create_room"):
        if not room_id:
            return None
        room = coordinator.rooms.get(room_id)
        if not room and username:
            p_obj = ConnectedPlayer(ws=None, ip_address="remote")
            p_obj.username = username
            p_obj.authenticated = True
            await coordinator.room_service.create_room(p_obj, coordinator.rooms, room_id=room_id)
            logger.info("Created new GameRoom '%s' via RoomService on server '%s'", room_id, SERVER_ID)
            try:
                redis = await get_redis()
                await redis.hset("room_routes", room_id, SERVER_ID)
            except Exception as e:
                logger.warning("Failed to record room_routes in Redis: %s", e)

        return {"status": ResponseStatus.CREATED.value, "room_id": room_id}

    # All other commands MUST resolve room from self.rooms and error if not found
    room = coordinator.rooms.get(room_id) if room_id else None
    if not room:
        logger.warning("Received room command '%s' for non-existent room '%s'", msg_type, room_id)
        if username:
            err_player = ConnectedPlayer(ws=None, ip_address="remote")
            err_player.username = username
            err_player.room_id = room_id
            await coordinator.send(err_player, ErrorMessage(message=MSG_ROOM_NOT_FOUND))
            return {"status": ResponseStatus.FAILED.value, "error": MSG_ROOM_NOT_FOUND}

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.authenticated = True
    player.room_id = room_id

    if room.white_player and room.white_player.username == username:
        player.color = Color.WHITE
    elif room.black_player and room.black_player.username == username:
        player.color = Color.BLACK

    if msg_type in (MessageType.JOIN_ROOM, MessageType.JOIN_ROOM.value, "join_room"):
        event, joined_room = await coordinator.room_service.join_room(player, room_id, coordinator.rooms)
        if event == RoomJoinEvent.GAME_CAN_START:
            await coordinator.game_session.start_game(joined_room)
            await coordinator.room_service.broadcast_room_state(joined_room)
        elif event in (RoomJoinEvent.RECONNECTED, RoomJoinEvent.SPECTATOR_ACTIVE):
            await coordinator.game_session.send_snapshot(player, joined_room)
    elif msg_type in (MessageType.MOVE, MessageType.MOVE.value, "move"):
        raw_str = json.dumps(cmd_data)
        await coordinator.game_session.process_move(player, deserialize_message(raw_str), coordinator.rooms)
    elif msg_type in (MessageType.JUMP, MessageType.JUMP.value, "jump"):
        raw_str = json.dumps(cmd_data)
        await coordinator.game_session.process_jump(player, deserialize_message(raw_str), coordinator.rooms)
    elif msg_type in (MessageType.LEAVE_ROOM, MessageType.LEAVE_ROOM.value, "leave_room"):
        await coordinator.room_service.leave_room(player, coordinator.rooms)
    elif msg_type in (MessageType.GET_SNAPSHOT, MessageType.GET_SNAPSHOT.value, "get_snapshot"):
        await coordinator.game_session.send_snapshot(player, room)

    return None


async def handle_room_join(data: RoomJoinPayload, reply_to: Optional[str]) -> None:
    room_id = data.room_id
    username = data.username
    if not room_id or not username:
        return

    room = coordinator.rooms.get(room_id)
    if not room:
        return

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.authenticated = True
    player.room_id = room_id

    event, joined_room = await coordinator.room_service.join_room(player, room_id, coordinator.rooms)
    if event == RoomJoinEvent.GAME_CAN_START:
        await coordinator.game_session.start_game(joined_room)
    await coordinator.room_service.broadcast_room_state(joined_room)


async def handle_room_leave(data: RoomLeavePayload, reply_to: Optional[str]) -> None:
    room_id = data.room_id
    username = data.username
    if not room_id or not username:
        return

    room = coordinator.rooms.get(room_id)
    if not room:
        return

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.authenticated = True
    player.room_id = room_id

    await coordinator.room_service.leave_room(player, coordinator.rooms)


async def main():
    await nats_bus.connect()
    logger.info("Game Server '%s' online. Subscribing to NATS topics...", SERVER_ID)
    await nats_bus.subscribe(GAME_ASSIGNED, handle_game_assigned, dto_class=GameAssignedPayload)
    await nats_bus.subscribe(GAME_COMMAND, handle_game_command, dto_class=GameCommandPayload)
    await nats_bus.subscribe(f"game.command.{SERVER_ID}", handle_game_command, dto_class=GameCommandPayload)
    await nats_bus.subscribe(ROOM_JOIN, handle_room_join, dto_class=RoomJoinPayload)
    await nats_bus.subscribe(ROOM_LEAVE, handle_room_leave, dto_class=RoomLeavePayload)

    await asyncio.Event().wait()



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Game Server '%s' shutting down.", SERVER_ID)
