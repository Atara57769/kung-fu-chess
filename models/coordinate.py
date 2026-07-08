from dataclasses import dataclass

@dataclass(frozen=True)
class Coordinate:
    y: int
    x: int
