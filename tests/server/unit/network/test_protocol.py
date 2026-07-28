import pytest
from shared.models.cell import Cell
from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
from shared.protocol.protocol import (
    serialize_snapshot, deserialize_snapshot
)


def test_snapshot_serialization():
    """Verify GameSnapshot objects serialize and deserialize correctly."""
    piece = PieceSnapshot(color="w", kind="K", cell=Cell(y=0, x=0), cooldown_until=0, status="IDLE")
    grid = ((piece, None), (None, None))
    board = BoardSnapshot(grid=grid, width=2, height=2)
    
    snapshot = GameSnapshot(
        board=board,
        selected_piece=piece,
        game_over=False,
        clock=100,
        pending_moves=(),
        jumps=()
    )
    
    serialized = serialize_snapshot(snapshot)
    deserialized = deserialize_snapshot(serialized)
    
    assert deserialized.clock == snapshot.clock
    assert deserialized.game_over == snapshot.game_over
    assert deserialized.board.width == snapshot.board.width
    assert deserialized.board.height == snapshot.board.height
    assert deserialized.selected_piece.color == "w"
    assert deserialized.selected_piece.kind == "K"
    assert deserialized.board.grid[0][0].color == "w"
    assert deserialized.board.grid[0][1] is None

def test_message_type_enum():
    """Verify MessageType enum values, string equality, and JSON serialization."""
    from shared.protocol import MessageType
    import json

    assert MessageType.AUTH == "auth"
    assert MessageType.ROOM_STATE == "room_state"
    assert MessageType.SNAPSHOT == "snapshot"
    assert MessageType.GAME_OVER == "game_over"

    # String equality and dict lookup
    assert MessageType("auth") == MessageType.AUTH
    assert MessageType.AUTH.value == "auth"

    # JSON serialization compatibility
    payload = {"type": MessageType.ROOM_STATE, "room_id": "1234"}
    serialized = json.dumps(payload)
    assert serialized == '{"type": "room_state", "room_id": "1234"}'
    deserialized = json.loads(serialized)
    assert deserialized["type"] == MessageType.ROOM_STATE

def test_message_dataclasses():
    """Verify message dataclasses serialize via asdict/serialize_message and deserialize via deserialize_message."""
    from dataclasses import asdict
    from shared.protocol import (
        MessageType, AuthMessage, AuthResponseMessage, RoomStateMessage, MoveMessage,
        ErrorMessage, GameOverMessage, serialize_message, deserialize_message
    )
    from shared.models.color import Color

    auth = AuthMessage(username="alice", password="pwd")
    assert auth.type == MessageType.AUTH
    auth_data = asdict(auth)
    assert auth_data == {"type": "auth", "username": "alice", "password": "pwd", "token": None}

    serialized_auth = serialize_message(auth)
    deserialized_auth = deserialize_message(serialized_auth)
    assert isinstance(deserialized_auth, AuthMessage)
    assert deserialized_auth.username == "alice"
    assert deserialized_auth.password == "pwd"
    assert deserialized_auth.type == MessageType.AUTH

    move = MoveMessage(from_cell=Cell(y=6, x=4), to_cell=Cell(y=4, x=4))
    assert move.type == MessageType.MOVE
    serialized_move = serialize_message(move)
    deserialized_move = deserialize_message(serialized_move)
    assert isinstance(deserialized_move, MoveMessage)
    assert deserialized_move.from_cell == Cell(y=6, x=4)
    assert deserialized_move.to_cell == Cell(y=4, x=4)
    assert deserialized_move.type == MessageType.MOVE


    room_state = RoomStateMessage(room_id="r1", your_color=Color.WHITE)
    assert room_state.your_color == Color.WHITE
    serialized_room = serialize_message(room_state)
    deserialized_room = deserialize_message(serialized_room)
    assert isinstance(deserialized_room, RoomStateMessage)
    assert deserialized_room.your_color == "w"



    auth_resp = AuthResponseMessage(success=True, username="alice", rating=1300)
    serialized_resp = serialize_message(auth_resp)
    deserialized_resp = deserialize_message(serialized_resp)
    assert isinstance(deserialized_resp, AuthResponseMessage)
    assert deserialized_resp.success is True
    assert deserialized_resp.username == "alice"
    assert deserialized_resp.rating == 1300

    err = ErrorMessage(message="Error occurred")
    serialized_err = serialize_message(err)
    parsed_err = deserialize_message(serialized_err)
    assert isinstance(parsed_err, ErrorMessage)
    assert parsed_err.message == "Error occurred"
    assert parsed_err.type == MessageType.ERROR

    game_over = GameOverMessage(winner="white", white_rating=1216, black_rating=1184)
    serialized_go = serialize_message(game_over)
    parsed_go = deserialize_message(serialized_go)
    assert isinstance(parsed_go, GameOverMessage)
    assert parsed_go.winner == "white"
    assert parsed_go.white_rating == 1216
    assert parsed_go.black_rating == 1184






