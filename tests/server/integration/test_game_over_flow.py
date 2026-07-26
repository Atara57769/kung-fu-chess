import asyncio
import os
import socket
import pytest
from server.network.server import GameServer
from client.network.client import GameClient
from shared.models.color import Color
from shared.models.cell import Cell

TEST_DB = os.path.join("tests", "server", "integration", "test_game_over_flow.db")

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

async def _run_game_over_flow():
    port = get_free_port()
    server = GameServer(host="127.0.0.1", port=port, db_path=TEST_DB)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)

    client_a = GameClient(host="127.0.0.1", port=port)
    client_b = GameClient(host="127.0.0.1", port=port)

    try:
        client_a.start()
        client_b.start()

        for _ in range(20):
            if client_a.ws is not None and client_b.ws is not None:
                break
            await asyncio.sleep(0.1)

        client_a.authenticate("p1", "pass")
        client_b.authenticate("p2", "pass")

        for _ in range(20):
            if client_a.authenticated and client_b.authenticated:
                break
            await asyncio.sleep(0.1)

        client_a.enter_matchmaking()
        client_b.enter_matchmaking()

        for _ in range(30):
            if client_a.current_snapshot is not None and client_b.current_snapshot is not None:
                break
            await asyncio.sleep(0.1)

        assert client_a.current_snapshot is not None
        assert client_b.current_snapshot is not None

        # Determine white and black clients
        white_client = client_a if client_a.your_color == Color.WHITE else client_b
        black_client = client_b if white_client == client_a else client_a

        # White moves e2 -> e4
        white_client.send_move(Cell(6, 4), Cell(4, 4))
        await asyncio.sleep(1.2)  # Wait for move execution (cooldown/movement time)

    finally:
        client_a.stop()
        client_b.stop()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

def test_game_over_flow(clean_db):
    asyncio.run(_run_game_over_flow())
