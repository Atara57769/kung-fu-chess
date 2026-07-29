import asyncio
import os
import socket
import tempfile
import pytest
from server.network.server import GameServer
from client.network.client import GameClient
from client.network.distributed_client import DistributedGameClient
from shared.security.ssl_config import generate_self_signed_cert, get_server_ssl_context, get_client_ssl_context
from shared.protocol import AuthMessage, AuthResponseMessage


def get_free_port() -> int:
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_generate_self_signed_cert():
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_p = os.path.join(tmpdir, "cert.pem")
        key_p = os.path.join(tmpdir, "key.pem")
        c_path, k_path = generate_self_signed_cert(cert_p, key_p)
        assert os.path.exists(c_path)
        assert os.path.exists(k_path)


def test_server_and_client_ssl_contexts():
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_p = os.path.join(tmpdir, "cert.pem")
        key_p = os.path.join(tmpdir, "key.pem")
        generate_self_signed_cert(cert_p, key_p)

        server_ctx = get_server_ssl_context(cert_path=cert_p, key_path=key_p, auto_generate=False)
        assert server_ctx is not None

        client_ctx = get_client_ssl_context(verify_ssl=False)
        assert client_ctx is not None


def test_distributed_client_ssl_instantiation():
    client_dist = DistributedGameClient(api_url="http://localhost:8000", use_ssl=True)
    assert client_dist.api_url.startswith("https://")
    assert client_dist.use_ssl is True
    assert client_dist.ssl_context is not None

    client_unencrypted = DistributedGameClient(api_url="http://localhost:8000", use_ssl=False)
    assert client_unencrypted.api_url == "http://localhost:8000"
    assert client_unencrypted.use_ssl is False
    assert client_unencrypted.ssl_context is None


async def _run_ssl_websocket_encrypted_connection():
    port = get_free_port()

    server = GameServer(host="127.0.0.1", port=port, use_ssl=True)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.3)

    client = GameClient(host="127.0.0.1", port=port, use_ssl=True, verify_ssl=False)
    try:
        client.start()
        for _ in range(30):
            if client.ws is not None:
                break
            await asyncio.sleep(0.1)

        assert client.ws is not None, "Client failed to connect via SSL WSS"
    finally:
        client.stop()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


def test_ssl_websocket_encrypted_connection():
    asyncio.run(_run_ssl_websocket_encrypted_connection())
