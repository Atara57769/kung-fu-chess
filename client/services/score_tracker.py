from shared.models.color import Color
from shared.models.piece_type import PieceType
from shared.constants import PIECE_POINTS

class ScoreTracker:
    def __init__(self, pubsub=None):
        self.white_score = 0
        self.black_score = 0
        self.pubsub = pubsub
        if self.pubsub is not None:
            self.pubsub.subscribe("snapshot", self.update)

    def get_score(self, color: str) -> int:
        """Exposes the current score for a given color (Color.WHITE or Color.BLACK)."""
        return self.white_score if color == Color.WHITE else self.black_score

    def update(self, snapshot) -> None:
        """Recalculates scores from the given game snapshot."""
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
