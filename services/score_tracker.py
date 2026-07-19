from models.color import Color
from models.piece_type import PieceType
from constants import PIECE_POINTS
from core.events import GameStarted, PieceCaptured, ScoreChanged

class ScoreTracker:
    def __init__(self, event_bus=None):
        self.white_score = 0
        self.black_score = 0
        self.event_bus = event_bus
        if self.event_bus is not None:
            self.event_bus.subscribe(GameStarted, self.on_game_started)
            self.event_bus.subscribe(PieceCaptured, self.on_piece_captured)

    def on_game_started(self, event: GameStarted) -> None:
        white = 0
        black = 0
        for color, kind in event.initial_pieces:
            points = PIECE_POINTS.get(kind, 0)
            if color == Color.WHITE:
                white += points
            elif color == Color.BLACK:
                black += points
        self.white_score = white
        self.black_score = black
        self.event_bus.publish(ScoreChanged(self.white_score, self.black_score))

    def on_piece_captured(self, event: PieceCaptured) -> None:
        points = PIECE_POINTS.get(event.victim_kind, 0)
        if event.victim_color == Color.WHITE:
            self.white_score = max(0, self.white_score - points)
        elif event.victim_color == Color.BLACK:
            self.black_score = max(0, self.black_score - points)
        self.event_bus.publish(ScoreChanged(self.white_score, self.black_score))

    def get_score(self, color: str) -> int:
        """Exposes the current score for a given color (Color.WHITE or Color.BLACK)."""
        return self.white_score if color == Color.WHITE else self.black_score

    def update(self, snapshot) -> None:
        """Recalculates scores from the given game snapshot (fallback/test mode)."""
        white = 0
        black = 0
        for row in snapshot.board.grid:
            for piece in row:
                if piece is not None:
                    points = PIECE_POINTS.get(piece.kind, 0)
                    if piece.color == Color.WHITE:
                        white += points
                    elif piece.color == Color.BLACK:
                        black += points
        self.white_score = white
        self.black_score = black

