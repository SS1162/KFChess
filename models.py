from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

@dataclass(frozen=True)
class BoardPosition:
    row: int
    col: int

@dataclass(frozen=True)
class Move:
    fr: int
    fc: int
    tr: int
    tc: int
