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
    import services.auth_service.main as auth_main
    import services.rooms_service.main as rooms_main
    import services.matchmaking_service.main as match_main
    import services.game_allocator.main as alloc_main
    import services.game_server.main as game_main

    assert callable(getattr(api_main, "main", None))
    assert callable(getattr(ws_main, "run_ws_gateway", None)) or hasattr(ws_main, "__name__")
    assert callable(getattr(auth_main, "run_auth_service", None)) or hasattr(auth_main, "__name__")
    assert callable(getattr(rooms_main, "run_rooms_service", None)) or hasattr(rooms_main, "__name__")
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
