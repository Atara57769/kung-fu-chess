import logging
from core.events.events import PieceMoved, PieceCaptured, GameEnded

logger = logging.getLogger(__name__)

class SoundManager:
    """Listens to game state events and triggers appropriate visual/auditory sound effect indicators."""
    
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        self.event_bus.subscribe(PieceMoved, self.on_piece_moved)
        self.event_bus.subscribe(PieceCaptured, self.on_piece_captured)
        self.event_bus.subscribe(GameEnded, self.on_game_ended)

    def on_piece_moved(self, event: PieceMoved) -> None:
        """Plays move sound indicator."""
        logger.info("[Sound Effect] Piece moved (swish)")

    def on_piece_captured(self, event: PieceCaptured) -> None:
        """Plays capture sound indicator."""
        kind_name = event.victim_kind.name if hasattr(event.victim_kind, 'name') else str(event.victim_kind)
        logger.info(f"[Sound Effect] {kind_name} captured (clash)")

    def on_game_ended(self, event: GameEnded) -> None:
        """Plays victory/defeat game over sound indicator."""
        winner_name = event.winner.name if hasattr(event.winner, 'name') else str(event.winner)
        # Handle case where event.winner might be Color enum or direct name string
        if winner_name == 'WHITE' or winner_name == 'w':
            winner_name = 'WHITE'
        elif winner_name == 'BLACK' or winner_name == 'b':
            winner_name = 'BLACK'
        logger.info(f"[Sound Effect] Game Ended! Winner: {winner_name} (fanfare)")

