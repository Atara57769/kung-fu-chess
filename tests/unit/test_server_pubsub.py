import pytest
import asyncio
from network.pubsub import PubSub, make_subscriber_callback
from network.models import ConnectedPlayer

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def send(self, message):
        self.sent_messages.append(message)

async def _run_pubsub_subscribe_publish_unsubscribe():
    pubsub = PubSub()
    ws = MockWebSocket()
    player = ConnectedPlayer(ws, "127.0.0.1")
    player.username = "test_user"

    received_messages = []

    async def mock_callback(message):
        received_messages.append(message)

    # 1. Test Subscribe & Publish
    pubsub.subscribe("room1", player, mock_callback)
    await pubsub.publish("room1", {"type": "game_update"})
    assert received_messages == [{"type": "game_update"}]

    # 2. Test Publish to another channel
    await pubsub.publish("room2", {"type": "other_update"})
    assert received_messages == [{"type": "game_update"}]

    # 3. Test Unsubscribe
    pubsub.unsubscribe("room1", player)
    await pubsub.publish("room1", {"type": "game_update_2"})
    assert received_messages == [{"type": "game_update"}]

def test_pubsub_subscribe_publish_unsubscribe():
    asyncio.run(_run_pubsub_subscribe_publish_unsubscribe())

async def _run_make_subscriber_callback():
    ws = MockWebSocket()
    player = ConnectedPlayer(ws, "127.0.0.1")
    player.username = "test_user"

    sent_data = []
    async def mock_send_json(websocket, data):
        sent_data.append((websocket, data))

    callback = make_subscriber_callback(player, mock_send_json)
    await callback({"type": "game_update"})

    assert len(sent_data) == 1
    assert sent_data[0][0] == ws
    assert sent_data[0][1] == {"type": "game_update"}

def test_make_subscriber_callback():
    asyncio.run(_run_make_subscriber_callback())
