import asyncio
import os
import socket
import pytest
from server.network.server import GameServer
from client.network.client import GameClient
from shared.models.color import Color

TEST_DB = os.path.join("server", "database", "test_net_kung_fu_chess.db")

def get_free_port() -> int:
    """Finds a free port on the host system to run the test server."""
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

async def _run_full_network_flow():
    port = get_free_port()
    
    server = GameServer(host="127.0.0.1", port=port, db_path=TEST_DB)
    
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Allow boot
    
    # 2. Setup Clients
    client_a = GameClient(host="127.0.0.1", port=port)
    client_b = GameClient(host="127.0.0.1", port=port)
    
    try:
        # Start background threads
        client_a.start()
        client_b.start()
        
        # Active wait for connections to establish
        for _ in range(20):
            if client_a.ws is not None and client_b.ws is not None:
                break
            await asyncio.sleep(0.1)
            
        assert client_a.ws is not None, "Client A failed to connect to WebSocket"
        assert client_b.ws is not None, "Client B failed to connect to WebSocket"
        
        # 3. Authenticate Client A
        client_a.authenticate("player1", "secret")
        for _ in range(20):
            if client_a.authenticated:
                break
            await asyncio.sleep(0.1)
        assert client_a.authenticated is True, "Client A authentication failed"
        
        # Authenticate Client B
        client_b.authenticate("player2", "secret")
        for _ in range(20):
            if client_b.authenticated:
                break
            await asyncio.sleep(0.1)
        assert client_b.authenticated is True, "Client B authentication failed"
        
        # 4. Join matchmaking
        client_a.enter_matchmaking()
        client_b.enter_matchmaking()
        
        # Active wait for pairing room status
        for _ in range(40):
            if client_a.room_state is not None and client_b.room_state is not None:
                break
            await asyncio.sleep(0.1)
            
        assert client_a.room_state is not None, "Client A failed to pair"
        assert client_b.room_state is not None, "Client B failed to pair"
        assert client_a.your_color in [Color.WHITE, Color.BLACK]
        assert client_b.your_color in [Color.WHITE, Color.BLACK]
        assert client_a.your_color != client_b.your_color
        
        # Active wait for first game state snapshot
        for _ in range(40):
            if client_a.current_snapshot is not None and client_b.current_snapshot is not None:
                break
            await asyncio.sleep(0.1)
            
        assert client_a.current_snapshot is not None, "Client A did not receive game snapshot"
        assert client_b.current_snapshot is not None, "Client B did not receive game snapshot"
        
    finally:
        # Guarantee cleanup even on failure
        client_a.stop()
        client_b.stop()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

def test_full_network_flow(clean_db):
    """Entry point wrapper using standard asyncio.run to execute the flow coro."""
    asyncio.run(_run_full_network_flow())
