import logging
from core.events.events import PieceMoved

logger = logging.getLogger(__name__)

class MoveLogger:
    """Subscribes to PieceMoved events and writes records to the application logger."""
    
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        self.event_bus.subscribe(PieceMoved, self.on_piece_moved)

    def on_piece_moved(self, event: PieceMoved) -> None:
        """Handler executed when a piece is successfully moved."""
        logger.info(f"Piece moved from {event.from_pos} to {event.to_pos}")
