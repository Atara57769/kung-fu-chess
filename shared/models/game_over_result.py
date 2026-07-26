from dataclasses import dataclass
from typing import Optional
from shared.models.color import Color

DEFAULT_WINNER_NAME = "draw"
WHITE_WINNER_KEYS = ("white", "w")
BLACK_WINNER_KEYS = ("black", "b")

KEY_WINNER = "winner"
KEY_MESSAGE = "message"
KEY_WHITE_RATING_CHANGE = "white_rating_change"
KEY_BLACK_RATING_CHANGE = "black_rating_change"


@dataclass
class GameOverResult:
    """Represents authoritative game completion data from the server."""
    winner: Optional[Color] = None
    winner_name: str = DEFAULT_WINNER_NAME
    message: str = ""
    white_rating_change: str = ""
    black_rating_change: str = ""


    @classmethod
    def from_message(cls, msg) -> "GameOverResult":
        raw_winner = str(getattr(msg, "winner", None) or DEFAULT_WINNER_NAME).lower()
        if raw_winner in WHITE_WINNER_KEYS:
            winner = Color.WHITE
        elif raw_winner in BLACK_WINNER_KEYS:
            winner = Color.BLACK
        else:
            winner = None

        return cls(
            winner=winner,
            winner_name=raw_winner,
            message=getattr(msg, "message", "") or "",
            white_rating_change=getattr(msg, "white_rating_change", "") or "",
            black_rating_change=getattr(msg, "black_rating_change", "") or ""
        )

