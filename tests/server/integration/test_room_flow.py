import asyncio
import os
import socket
import pytest
from server.network.server import GameServer
from client.network.client import GameClient
from shared.models.color import Color

TEST_DB = os.path.join("tests", "server", "integration", "test_room_flow.db")

def get_free_port() -> int:
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@pytest.fixture
def clean_db():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

async def _run_room_flow():
    port = get_free_port()
    server = GameServer(host="127.0.0.1", port=port, db_path=TEST_DB)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)

    client_creator = GameClient(host="127.0.0.1", port=port)
    client_joiner = GameClient(host="127.0.0.1", port=port)

    try:
        client_creator.start()
        client_joiner.start()

        for _ in range(20):
            if client_creator.ws is not None and client_joiner.ws is not None:
                break
            await asyncio.sleep(0.1)

        client_creator.authenticate("creator", "pass")
        client_joiner.authenticate("joiner", "pass")

        for _ in range(20):
            if client_creator.authenticated and client_joiner.authenticated:
                break
            await asyncio.sleep(0.1)

        # Creator creates room
        client_creator.create_room("custom123")
        for _ in range(20):
            if client_creator.room_state is not None:
                break
            await asyncio.sleep(0.1)

        assert client_creator.room_state is not None
        assert client_creator.room_state.room_id == "custom123"
        assert client_creator.room_state.white == "creator"
        assert client_creator.your_color == Color.WHITE

        # Joiner joins room
        client_joiner.join_room("custom123")
        for _ in range(20):
            if client_joiner.room_state is not None and client_joiner.room_state.black == "joiner":
                break
            await asyncio.sleep(0.1)

        assert client_joiner.room_state is not None
        assert client_joiner.room_state.black == "joiner"
        assert client_joiner.your_color == Color.BLACK

        # Joiner leaves room
        client_joiner.leave_room()
        for _ in range(20):
            if client_joiner.room_state and client_joiner.room_state.room_id is None:
                break
            await asyncio.sleep(0.1)

        assert client_joiner.room_state.room_id is None

    finally:
        client_creator.stop()
        client_joiner.stop()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

def test_room_flow(clean_db):
    asyncio.run(_run_room_flow())
