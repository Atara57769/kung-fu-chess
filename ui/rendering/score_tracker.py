from models.game_snapshot import GameSnapshot
import ui.ui_config as cfg
from models.color import Color

class ScoreTracker:
    def __init__(self):
        self.white_score = 0
        self.black_score = 0

    def update(self, snapshot: GameSnapshot) -> None:
        """Recalculates scores from the given game snapshot."""
        white = 0
        black = 0
        for row in snapshot.board.grid:
            for piece in row:
                if piece is not None:
                    points = cfg.PIECE_POINTS.get(piece.kind, 0)
                    if piece.color == Color.WHITE:
                        white += points
                    elif piece.color == Color.BLACK:
                        black += points
        self.white_score = white
        self.black_score = black

    def get_score(self, color: str) -> int:
        """Exposes the current score for a given color (Color.WHITE or Color.BLACK)."""
        return self.white_score if color == Color.WHITE else self.black_score

