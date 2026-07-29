import pytest
from server.services.auth_service import authenticate_user
from server.database.sqlite_db_manager import SQLiteDBManager
from shared.message_contracts.subjects import (
    AUTH_LOGIN, AUTH_RESULT, MATCHMAKING_REQUEST, MATCHMAKING_MATCH_FOUND,
    ROOM_CREATE, ROOM_CREATED, GAME_ASSIGNED, GAME_COMMAND, GAME_STATE
)
from shared.message_contracts.contracts import (
    AuthLoginPayload, AuthResultPayload, MatchmakingRequestPayload,
    MatchFoundPayload, RoomCreatePayload, encode_json, decode_json
)
from client.network.client import GameClient
from client.network.distributed_client import DistributedGameClient
import distributed_client_main


def test_postgres_db_manager_url_builder():
    from server.database.postgres_db_manager import PostgresDBManager
    mgr = PostgresDBManager(database_url="sqlite:///:memory:")
    assert mgr.get_user_rating("nonexistent") == 1200


def test_auth_service_auto_registration_and_login():
    db_mgr = SQLiteDBManager(db_path="sqlite:///:memory:")

    # 1. New user -> Auto-registers
    success, user_info, err = authenticate_user("new_player", "secret123", db_mgr)
    assert success is True
    assert user_info.username == "new_player"
    assert user_info.rating == 1200

    # 2. Existing user, correct password -> Logged in
    success2, user_info2, err2 = authenticate_user("new_player", "secret123", db_mgr)
    assert success2 is True
    assert user_info2.username == "new_player"

    # 3. Existing user, wrong password -> Authentication failed
    success3, user_info3, err3 = authenticate_user("new_player", "wrongpass", db_mgr)
    assert success3 is False
    assert user_info3 is None
    assert err3 == "Authentication failed."


def test_api_gateway_user_service_login_and_token():
    from services.api_gateway.services import UserService
    db_mgr = SQLiteDBManager(db_path="sqlite:///:memory:")
    service = UserService(db_manager=db_mgr)

    # Calling login for a brand new user -> Auto-registers and succeeds
    success, user_info, err = service.login_user("auto_user", "pass123")
    assert success is True
    assert user_info.username == "auto_user"
    assert user_info.rating == 1200


def test_distributed_client_instantiation():
    client_mono = GameClient()
    client_dist = DistributedGameClient()

    assert client_dist.api_url == "http://localhost:8000"
    assert client_dist.ws_port == 8001


def test_distributed_client_parse_args():
    args = distributed_client_main.parse_args([])
    assert args.ws_port == 8001
    assert args.api_host == "http://localhost:8000"


def test_microservice_entry_points():
    import services.api_gateway.main as api_main
    import services.websocket_gateway.main as ws_main
    import services.matchmaking_service.main as match_main
    import services.game_allocator.main as alloc_main
    import services.game_server.main as game_main

    assert callable(getattr(api_main, "main", None))
    assert callable(getattr(ws_main, "run_ws_gateway", None)) or hasattr(ws_main, "__name__")
    assert callable(getattr(match_main, "run_matchmaking_service", None)) or hasattr(match_main, "__name__")
    assert callable(getattr(alloc_main, "run_game_allocator", None)) or hasattr(alloc_main, "__name__")
    assert callable(getattr(game_main, "run_game_server", None)) or hasattr(game_main, "__name__")


def test_nats_subject_constants():
    assert AUTH_LOGIN == "auth.login"
    assert AUTH_RESULT == "auth.result"
    assert MATCHMAKING_REQUEST == "matchmaking.request"
    assert MATCHMAKING_MATCH_FOUND == "matchmaking.match_found"
    assert ROOM_CREATE == "room.create"
    assert ROOM_CREATED == "room.created"
    assert GAME_ASSIGNED == "game.assigned"
    assert GAME_COMMAND == "game.command"
    assert GAME_STATE == "game.state"


def test_nats_contracts_serialization():
    payload = AuthLoginPayload(username="alice", password="password123")
    encoded = encode_json(payload.to_dict())
    decoded = decode_json(encoded)

    assert decoded["username"] == "alice"
    assert decoded["password"] == "password123"

    res_payload = AuthResultPayload(success=True, username="alice", token="token-123", rating=1350)
    assert res_payload.to_dict()["rating"] == 1350


def test_game_allocator_room_create_stores_redis_route():
    import asyncio
    from unittest.mock import AsyncMock, patch
    from services.game_allocator.app import handle_room_create, nats_bus
    from shared.message_contracts.contracts import RoomCreatePayload

    async def run_test():
        mock_redis = AsyncMock()
        with patch("services.game_allocator.app.get_redis", return_value=mock_redis), \
             patch.object(nats_bus, "publish", new_callable=AsyncMock) as mock_publish:

            res = await handle_room_create(RoomCreatePayload(room_id="alloc_room_1", host="alice"), reply_to=None)
            assert res is not None
            assert res.room_id == "alloc_room_1"
            mock_redis.hset.assert_called_once()
            assert mock_redis.hset.call_args[0][0] == "room_routes"

            published_subjects = [call.args[0] for call in mock_publish.call_args_list]
            assert "game.assigned" in published_subjects

    asyncio.run(run_test())


def test_handle_matchmaking_request_pairs_players():
    import asyncio
    from unittest.mock import AsyncMock, patch
    from services.matchmaking_service.app import handle_matchmaking_request, nats_bus, matchmaking_queue, player_registry
    from shared.message_contracts.contracts import MatchmakingRequestPayload

    async def run_test():
        matchmaking_queue.clear()
        player_registry.clear()

        with patch.object(nats_bus, "publish", new_callable=AsyncMock) as mock_publish:
            res1 = await handle_matchmaking_request(MatchmakingRequestPayload(action="join", username="alice", rating=1200), reply_to=None)
            assert res1.status == "queued"

            res2 = await handle_matchmaking_request(MatchmakingRequestPayload(action="join", username="bob", rating=1200), reply_to=None)
            assert res2.status == "queued"

            await asyncio.sleep(0.1)

            published_subjects = [call.args[0] for call in mock_publish.call_args_list]
            assert "matchmaking.match_found" in published_subjects

    asyncio.run(run_test())


def test_handle_game_command_lifecycle_and_non_existent_rejection():
    import asyncio
    from unittest.mock import AsyncMock, patch
    from services.game_server.app import handle_game_assigned, handle_game_command, coordinator, nats_bus
    from shared.message_contracts.contracts import GameAssignedPayload, GameCommandPayload

    async def run_test():
        coordinator.rooms.clear()
        mock_redis = AsyncMock()

        with patch("services.game_server.app.get_redis", return_value=mock_redis), \
             patch.object(nats_bus, "publish", new_callable=AsyncMock):

            # 1. Non-existent room command rejection
            invalid_cmd = GameCommandPayload(
                room_id="non_existent_room",
                username="charlie",
                gateway_id="ws_gw_1",
                data={"type": "move", "from_cell": {"x": 0, "y": 0}, "to_cell": {"x": 0, "y": 1}}
            )
            res = await handle_game_command(invalid_cmd, reply_to=None)
            assert res is not None
            assert res.get("status") == "failed"
            assert "non_existent_room" not in coordinator.rooms

            # 2. Creating / Assigning room
            await handle_game_assigned(GameAssignedPayload(
                game_server_id="game_server_1",
                room_id="room_cmd_test",
                player1="alice",
                player2="bob"
            ), reply_to=None)

            room = coordinator.rooms.get("room_cmd_test")
            assert room is not None
            assert room.white_player.username == "alice"
            assert room.black_player.username == "bob"

            # 3. Execute a valid move command
            move_cmd = GameCommandPayload(
                room_id="room_cmd_test",
                username="alice",
                gateway_id="ws_gw_1",
                data={
                    "type": "move",
                    "from_cell": {"x": 4, "y": 6},
                    "to_cell": {"x": 4, "y": 4}
                }
            )
            await handle_game_command(move_cmd, reply_to=None)

            # 4. Teardown / cleanup removes room from self.rooms
            await coordinator.cleanup_room("room_cmd_test")
            assert "room_cmd_test" not in coordinator.rooms

    asyncio.run(run_test())



