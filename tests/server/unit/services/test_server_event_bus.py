import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from server.services.server_event_bus import ServerEventBus, ServerEventType, ServerEvent
from server.services.server_event_listener import ServerEventListener
from server.network.models import ConnectedPlayer, GameRoom
from shared.protocol import RoomStateMessage, SnapshotMessage, AuthResponseMessage, ErrorMessage


def test_server_event_bus_subscribe_publish():
    async def _test():
        bus = ServerEventBus()
        received_events = []

        async def callback(event: ServerEvent):
            received_events.append(event)

        bus.subscribe(ServerEventType.ROOM_STATE_CHANGED, callback)
        await bus.publish(ServerEventType.ROOM_STATE_CHANGED, target="room_1", data={"key": "val"})

        assert len(received_events) == 1
        assert received_events[0].event_type == ServerEventType.ROOM_STATE_CHANGED
        assert received_events[0].target == "room_1"
        assert received_events[0].data == {"key": "val"}

    asyncio.run(_test())


def test_server_event_bus_unsubscribe():
    async def _test():
        bus = ServerEventBus()
        received_events = []

        async def callback(event: ServerEvent):
            received_events.append(event)

        bus.subscribe(ServerEventType.ERROR_MESSAGE, callback)
        await bus.publish(ServerEventType.ERROR_MESSAGE, data="err1")
        assert len(received_events) == 1

        bus.unsubscribe(ServerEventType.ERROR_MESSAGE, callback)
        await bus.publish(ServerEventType.ERROR_MESSAGE, data="err2")
        assert len(received_events) == 1

    asyncio.run(_test())


def test_server_event_listener_room_state():
    async def _test():
        bus = ServerEventBus()
        mock_send = AsyncMock()
        listener = ServerEventListener(bus, send=mock_send)

        ws_mock = MagicMock()
        player = ConnectedPlayer(ws=ws_mock, ip="127.0.0.1")
        player.username = "Alice"

        room = GameRoom("room_123")
        room.white_player = player

        await bus.publish(ServerEventType.ROOM_STATE_CHANGED, target=room)

        assert mock_send.called
        ws_arg, msg_arg = mock_send.call_args[0]
        assert ws_arg == ws_mock
        assert isinstance(msg_arg, RoomStateMessage)
        assert msg_arg.room_id == "room_123"
        assert msg_arg.white == "Alice"

    asyncio.run(_test())


def test_server_event_listener_auth_response():
    async def _test():
        bus = ServerEventBus()
        mock_send = AsyncMock()
        listener = ServerEventListener(bus, send=mock_send)

        ws_mock = MagicMock()
        player = ConnectedPlayer(ws=ws_mock, ip="127.0.0.1")

        auth_msg = AuthResponseMessage(success=True, username="Bob", rating=1200)
        await bus.publish(ServerEventType.AUTH_RESPONSE, target=player, data=auth_msg)

        mock_send.assert_called_once_with(ws_mock, auth_msg)

    asyncio.run(_test())


def test_server_event_listener_error_message():
    async def _test():
        bus = ServerEventBus()
        mock_send = AsyncMock()
        listener = ServerEventListener(bus, send=mock_send)

        ws_mock = MagicMock()
        player = ConnectedPlayer(ws=ws_mock, ip="127.0.0.1")

        await bus.publish(ServerEventType.ERROR_MESSAGE, target=player, data="Access Denied")

        assert mock_send.called
        ws_arg, msg_arg = mock_send.call_args[0]
        assert ws_arg == ws_mock
        assert isinstance(msg_arg, ErrorMessage)
        assert msg_arg.message == "Access Denied"

    asyncio.run(_test())
