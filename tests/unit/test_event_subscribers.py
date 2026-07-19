import logging
from core.events.event_bus import EventBus
from core.events.events import PieceMoved, PieceCaptured, GameEnded
from models.cell import Cell
from models.color import Color
from models.piece_type import PieceType
from services.move_logger import MoveLogger
from services.sound_manager import SoundManager

def test_move_logger_subscribes_and_logs(caplog):
    """Verify MoveLogger logs the message on PieceMoved event."""
    event_bus = EventBus()
    move_logger = MoveLogger(event_bus)
    
    with caplog.at_level(logging.INFO):
        event_bus.publish(PieceMoved(from_pos=Cell(0, 0), to_pos=Cell(1, 1)))
        
    assert any("Piece moved from Cell(y=0, x=0) to Cell(y=1, x=1)" in rec.message for rec in caplog.records)

def test_sound_manager_subscribes_and_logs(caplog):
    """Verify SoundManager logs appropriate sound messages for events."""
    event_bus = EventBus()
    sound_manager = SoundManager(event_bus)
    
    with caplog.at_level(logging.INFO):
        event_bus.publish(PieceMoved(from_pos=Cell(0, 0), to_pos=Cell(1, 1)))
        event_bus.publish(PieceCaptured(
            attacker_color=Color.WHITE,
            victim_color=Color.BLACK,
            victim_kind=PieceType.ROOK
        ))
        event_bus.publish(GameEnded(winner=Color.WHITE))
        
    messages = [rec.message for rec in caplog.records]
    assert any("[Sound Effect] Piece moved (swish)" in msg for msg in messages)
    assert any("[Sound Effect] ROOK captured (clash)" in msg for msg in messages)
    assert any("[Sound Effect] Game Ended! Winner: WHITE (fanfare)" in msg for msg in messages)
