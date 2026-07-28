import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional

from shared.constants import ResponseStatus, ROOM_STATUS_ACTIVE
from shared.protocol import (
    MessageType,
    deserialize_message,
    serialize_message,
    RoomStateMessage
)
from shared.models.color import Color
from shared.message_contracts.subjects import (
    GAME_ASSIGNED, GAME_COMMAND, GAME_STATE, GAME_FINISHED, GAME_EVENTS
)
from shared.message_contracts.contracts import (
    GameStatePayload, GameAssignedPayload, GameFinishedPayload
)
from shared.message_contracts.nats_client import NatsBus
from server.network.models import GameRoom, ConnectedPlayer
from server.database.sqlite_db_manager import SQLiteDBManager
from server.database.postgres_db_manager import PostgresDBManager
from server.services.game_coordinator import GameCoordinator

SERVER_ID = os.getenv("SERVER_ID", "game_server_1")
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [%(levelname)s] GameServer[{SERVER_ID}]: %(message)s")
logger = logging.getLogger(f"GameServer[{SERVER_ID}]")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
db_manager = PostgresDBManager()
nats_bus = NatsBus(url=NATS_URL)


class NatsGameCoordinator(GameCoordinator):
    """Subclass of GameCoordinator adapted for NATS event bus communication."""

    def __init__(self, db=db_manager):
        super().__init__(db=db)
        self.set_send(self._nats_send)

    async def _nats_send(self, ws_target, message_obj: Any) -> None:
        """Publishes game state snapshots and events to NATS subject using GameStatePayload DTO."""
        if hasattr(message_obj, "__dict__"):
            data = message_obj.__dict__
        else:
            data = message_obj

        raw = serialize_message(message_obj) if not isinstance(data, str) else data
        target_user = getattr(ws_target, "username", None) if hasattr(ws_target, "username") else None
        room_id = getattr(ws_target, "room_id", None)
        state_content = json.loads(raw) if isinstance(raw, str) and raw.startswith("{") else raw

        payload_dto = GameStatePayload(
            room_id=room_id,
            state=state_content,
            target_username=target_user
        )
        await nats_bus.publish(GAME_STATE, payload_dto)


coordinator = NatsGameCoordinator(db=db_manager)


async def handle_game_assigned(data: Dict[str, Any], reply_to: Optional[str]) -> Optional[Dict[str, Any]]:
    target_server = data.get("game_server_id")
    if target_server and target_server != SERVER_ID:
        return None

    room_id = data.get("room_id")
    player1 = data.get("player1")
    player2 = data.get("player2")

    if not room_id or not player1 or not player2:
        return None

    logger.info("Initializing game session for room '%s' (%s vs %s)", room_id, player1, player2)

    room = GameRoom(room_id=room_id)
    p1_obj = ConnectedPlayer(ws=None, ip_address="remote")
    p1_obj.username = player1
    p1_obj.authenticated = True
    p1_obj.color = Color.WHITE
    p1_obj.room_id = room_id

    p2_obj = ConnectedPlayer(ws=None, ip_address="remote")
    p2_obj.username = player2
    p2_obj.authenticated = True
    p2_obj.color = Color.BLACK
    p2_obj.room_id = room_id

    room.white_player = p1_obj
    room.black_player = p2_obj
    coordinator.rooms[room_id] = room

    # Start authoritative game engine loop for this session
    await coordinator.game_session.start_game(room)
    logger.info("Game engine loop active for room '%s'", room_id)

    # Broadcast initial ACTIVE room state to both players so client UIs switch to OnlineGameScreen
    p1_state_msg = RoomStateMessage(
        room_id=room_id,
        status=ROOM_STATUS_ACTIVE,
        white=player1,
        black=player2,
        your_color=Color.WHITE.value
    )
    p2_state_msg = RoomStateMessage(
        room_id=room_id,
        status=ROOM_STATUS_ACTIVE,
        white=player1,
        black=player2,
        your_color=Color.BLACK.value
    )

    await nats_bus.publish(GAME_STATE, GameStatePayload(
        room_id=room_id,
        state=json.loads(serialize_message(p1_state_msg)),
        target_username=player1
    ))
    await nats_bus.publish(GAME_STATE, GameStatePayload(
        room_id=room_id,
        state=json.loads(serialize_message(p2_state_msg)),
        target_username=player2
    ))

    return {"status": ResponseStatus.STARTED.value, "room_id": room_id, "server_id": SERVER_ID}


async def handle_game_command(data: Dict[str, Any], reply_to: Optional[str]) -> Optional[Dict[str, Any]]:
    room_id = data.get("room_id")
    username = data.get("username")
    cmd_data = data.get("data", {})
    msg_type = cmd_data.get("type")

    if not room_id or room_id not in coordinator.rooms:
        if msg_type == MessageType.CREATE_ROOM and room_id:
            room = GameRoom(room_id=room_id)
            coordinator.rooms[room_id] = room
            logger.info("Dynamically created room '%s'", room_id)
        else:
            return None

    room = coordinator.rooms.get(room_id)
    if not room:
        return None

    player = ConnectedPlayer(ws=None, ip_address="remote")
    player.username = username
    player.authenticated = True
    player.room_id = room_id

    if room.white_player and room.white_player.username == username:
        player.color = Color.WHITE
    elif room.black_player and room.black_player.username == username:
        player.color = Color.BLACK

    if msg_type in (MessageType.MOVE, MessageType.MOVE.value, "move"):
        raw_str = json.dumps(cmd_data)
        await coordinator.game_session.process_move(player, deserialize_message(raw_str), coordinator.rooms)
    elif msg_type in (MessageType.JUMP, MessageType.JUMP.value, "jump"):
        raw_str = json.dumps(cmd_data)
        await coordinator.game_session.process_jump(player, deserialize_message(raw_str), coordinator.rooms)
    elif msg_type in (MessageType.GET_SNAPSHOT, MessageType.GET_SNAPSHOT.value, "get_snapshot"):
        await coordinator.game_session.send_snapshot(player, room)

    return None


async def main():
    await nats_bus.connect()
    logger.info("Game Server '%s' online. Subscribing to NATS topics...", SERVER_ID)
    await nats_bus.subscribe(GAME_ASSIGNED, handle_game_assigned)
    await nats_bus.subscribe(GAME_COMMAND, handle_game_command)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Game Server '%s' shutting down.", SERVER_ID)
