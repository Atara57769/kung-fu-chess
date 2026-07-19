import pytest
from core.events import (
    EventBus,
    PieceMoved,
    PieceCaptured,
    ScoreChanged,
    GameStarted,
    GameEnded,
)

def test_event_bus_subscribe_and_publish():
    bus = EventBus()
    calls = []

    def on_piece_moved(event: PieceMoved):
        calls.append(event.move)

    bus.subscribe(PieceMoved, on_piece_moved)
    bus.publish(PieceMoved(move="e2e4"))

    assert calls == ["e2e4"]


def test_event_bus_multiple_subscribers():
    bus = EventBus()
    calls_a = []
    calls_b = []

    bus.subscribe(GameStarted, lambda e: calls_a.append(True))
    bus.subscribe(GameStarted, lambda e: calls_b.append(True))

    bus.publish(GameStarted())

    assert len(calls_a) == 1
    assert len(calls_b) == 1


def test_event_bus_unsubscribe():
    bus = EventBus()
    calls = []

    def callback(event: GameEnded):
        calls.append(event.winner)

    bus.subscribe(GameEnded, callback)
    bus.publish(GameEnded(winner="white"))
    assert calls == ["white"]

    bus.unsubscribe(GameEnded, callback)
    bus.publish(GameEnded(winner="black"))
    # Should not call the callback again
    assert calls == ["white"]


def test_event_bus_unsubscribe_non_existent():
    bus = EventBus()
    # Unsubscribing when no subscribers exist at all
    bus.unsubscribe(PieceMoved, lambda e: None)

    # Unsubscribing a callback that isn't registered, but others are
    callback_1 = lambda e: None
    callback_2 = lambda e: None
    bus.subscribe(PieceMoved, callback_1)
    bus.unsubscribe(PieceMoved, callback_2)
    # The callback_1 should still be registered
    assert PieceMoved in bus._subscribers
    assert bus._subscribers[PieceMoved] == [callback_1]


def test_event_bus_publish_no_subscribers():
    bus = EventBus()
    # Publishing should do nothing and not raise any error
    bus.publish(ScoreChanged(white_score=1, black_score=0))


def test_event_bus_event_isolation():
    bus = EventBus()
    captured_calls = []
    moved_calls = []

    bus.subscribe(PieceCaptured, lambda e: captured_calls.append(e))
    bus.subscribe(PieceMoved, lambda e: moved_calls.append(e))

    bus.publish(PieceMoved(move="d2d4"))

    assert len(moved_calls) == 1
    assert len(captured_calls) == 0


def test_event_bus_unsubscribe_during_publish():
    bus = EventBus()
    calls = []

    def callback(event: PieceMoved):
        calls.append(event.move)
        bus.unsubscribe(PieceMoved, callback)

    bus.subscribe(PieceMoved, callback)
    bus.publish(PieceMoved(move="e2e4"))
    bus.publish(PieceMoved(move="e7e5"))

    assert calls == ["e2e4"]
