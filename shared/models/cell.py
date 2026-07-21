from dataclasses import dataclass

@dataclass(frozen=True)
class Cell:
    y: int
    x: int
