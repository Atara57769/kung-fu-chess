import asyncio
import os
import socket
import pytest
from server.network.server import GameServer
from client.network.client import GameClient

TEST_DB = os.path.join("tests", "server", "integration", "test_auth_flow.db")

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

async def _run_auth_flow():
    port = get_free_port()
    server = GameServer(host="127.0.0.1", port=port, db_path=TEST_DB)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)

    client = GameClient(host="127.0.0.1", port=port)
    try:
        client.start()
        for _ in range(20):
            if client.ws is not None:
                break
            await asyncio.sleep(0.1)

        assert client.ws is not None

        # Auto-registration & Auth
        client.authenticate("test_user", "password123")
        for _ in range(20):
            if client.authenticated:
                break
            await asyncio.sleep(0.1)

        assert client.authenticated is True
        assert client.username == "test_user"
        assert client.rating == 1200

        # Disconnect client
        client.stop()
        await asyncio.sleep(0.1)

        # Re-connect client with wrong password
        client_bad = GameClient(host="127.0.0.1", port=port)
        client_bad.start()
        for _ in range(20):
            if client_bad.ws is not None:
                break
            await asyncio.sleep(0.1)

        client_bad.authenticate("test_user", "wrong_pass")
        for _ in range(20):
            if client_bad.error_message is not None:
                break
            await asyncio.sleep(0.1)

        assert client_bad.authenticated is False
        assert client_bad.error_message == "Authentication failed."
        client_bad.stop()

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

def test_auth_flow(clean_db):
    asyncio.run(_run_auth_flow())
