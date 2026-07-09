from dataclasses import dataclass

from models import Point

@dataclass(frozen=True)
class ClickCommand:
    p: Point


@dataclass(frozen=True)
class WaitCommand:
    ms: int


@dataclass(frozen=True)
class PrintBoardCommand:
    pass


@dataclass(frozen=True)
class JumpCommand:
    p: Point
