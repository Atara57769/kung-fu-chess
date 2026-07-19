from dataclasses import dataclass

@dataclass
class PieceMoved:
    move: str

@dataclass
class PieceCaptured:
    attacker: str
    victim: str

@dataclass
class ScoreChanged:
    white_score: int
    black_score: int

@dataclass
class GameStarted:
    pass

@dataclass
class GameEnded:
    winner: str
