import gc
import pytest
from unittest.mock import MagicMock
from client.services.client_pubsub import ClientPubSub
from client.services.score_tracker import ScoreTracker
from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
from shared.models.cell import Cell
from shared.models.color import Color
from shared.models.piece_type import PieceType

class SubscriberMock:
    def __init__(self):
        self.events = []

    def on_event(self, *args, **kwargs):
        self.events.append((args, kwargs))

def test_client_pubsub_basic():
    pubsub = ClientPubSub()
    sub = SubscriberMock()
    
    # 1. Test Subscribe & Publish
    pubsub.subscribe("test_event", sub.on_event)
    pubsub.publish("test_event", "hello", value=42)
    
    assert len(sub.events) == 1
    assert sub.events[0] == (("hello",), {"value": 42})
    
    # 2. Test Unsubscribe
    pubsub.unsubscribe("test_event", sub.on_event)
    pubsub.publish("test_event", "world")
    assert len(sub.events) == 1  # No new event received

def test_client_pubsub_weakref():
    pubsub = ClientPubSub()
    sub = SubscriberMock()
    
    pubsub.subscribe("event_x", sub.on_event)
    
    # Verify it works initially
    pubsub.publish("event_x", 1)
    assert len(sub.events) == 1
    
    # Delete the subscriber instance
    del sub
    gc.collect()  # Force garbage collection
    
    # Publish again (should not crash and should clean up internal list)
    pubsub.publish("event_x", 2)
    assert len(pubsub._subscribers.get("event_x", [])) == 0

def test_score_tracker_pubsub_integration():
    pubsub = ClientPubSub()
    score_tracker = ScoreTracker(pubsub)
    
    grid = [[None for _ in range(8)] for _ in range(8)]
    grid[0][0] = PieceSnapshot(Color.WHITE, PieceType.ROOK.value, Cell(0, 0))
    grid[1][1] = PieceSnapshot(Color.BLACK, PieceType.PAWN.value, Cell(1, 1))
    
    grid_snapshot = tuple(tuple(row) for row in grid)
    board = BoardSnapshot(grid=grid_snapshot, width=8, height=8)
    
    snapshot = GameSnapshot(
        board=board,
        selected_piece=None,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )
    
    # Trigger snapshot received event
    pubsub.publish("snapshot", snapshot)
    
    # Verify score tracker was updated via pubsub event
    assert score_tracker.white_score == 5
    assert score_tracker.black_score == 1
