import time
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.constants import CLIENT_PING_TIMEOUT
from shared.message_contracts.contracts import PlayerDisconnectedPayload
from shared.message_contracts.subjects import PLAYER_DISCONNECTED
from shared.protocol import MessageType, HeartbeatAckMessage, serialize_message

from services.websocket_gateway.app import (
    GatewaySession, active_sockets, handle_client_message, ping_monitor_loop, GATEWAY_ID
)
from services.game_server.app import handle_player_disconnected as game_server_handle_disconnect, coordinator
from services.matchmaking_service.app import handle_player_disconnected as matchmaking_handle_disconnect


@pytest.mark.anyio
async def test_ping_message_updates_last_ping():
    ws = MagicMock()
    ws.send = AsyncMock()
    session = GatewaySession(authenticated=True, username="test_user")
    active_sockets[ws] = session

    old_ping = time.time() - 10.0
    session.last_ping = old_ping

    # Send ping message
    ping_msg = '{"type": "ping"}'
    await handle_client_message(ws, ping_msg)

    assert session.last_ping > old_ping
    ws.send.assert_called_once()
    active_sockets.pop(ws, None)


@pytest.mark.anyio
async def test_ping_monitor_loop_publishes_event_and_closes_socket():
    ws = MagicMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    session = GatewaySession(authenticated=True, username="inactive_user")
    # Simulate last_ping > 20s ago
    session.last_ping = time.time() - 25.0
    active_sockets[ws] = session

    published_events = []

    async def mock_publish(subject, payload):
        published_events.append((subject, payload))

    with patch("services.websocket_gateway.app.nats_bus.publish", side_effect=mock_publish):
        # Run one iteration of monitor loop
        task = asyncio.create_task(ping_monitor_loop())
        await asyncio.sleep(1.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    ws.close.assert_called_once()
    assert len(published_events) == 1
    subject, payload = published_events[0]
    assert subject == PLAYER_DISCONNECTED
    assert payload.username == "inactive_user"
    assert payload.reason == "ping_timeout"

    active_sockets.pop(ws, None)


@pytest.mark.anyio
async def test_game_server_handles_player_disconnected_event():
    with patch.object(coordinator, "handle_disconnect", new_callable=AsyncMock) as mock_handle_disc:
        # Set up a dummy room with player
        mock_room = MagicMock()
        mock_room.white_player = MagicMock(username="disconnected_player")
        mock_room.black_player = MagicMock(username="opponent")
        mock_room.spectators = []
        coordinator.rooms["room_123"] = mock_room

        payload = PlayerDisconnectedPayload(gateway_id="gw1", username="disconnected_player", reason="ping_timeout")
        await game_server_handle_disconnect(payload, None)

        mock_handle_disc.assert_called_once()
        coordinator.rooms.pop("room_123", None)


@pytest.mark.anyio
async def test_matchmaking_service_handles_player_disconnected_event():
    with patch("services.matchmaking_service.app.redis_dequeue", new_callable=AsyncMock) as mock_dequeue, \
         patch("services.matchmaking_service.app.get_redis", new_callable=AsyncMock) as mock_get_redis:
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        payload = PlayerDisconnectedPayload(gateway_id="gw1", username="queued_player", reason="ping_timeout")
        await matchmaking_handle_disconnect(payload, None)

        mock_dequeue.assert_called_once_with("queued_player")
        mock_redis.delete.assert_called_once_with("player_match:queued_player")
