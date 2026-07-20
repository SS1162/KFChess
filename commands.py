from dataclasses import dataclass

from models import Point

@dataclass(frozen=True)
class ClickCommand:
    p: Point
    cell_size: int = 0  # 0 means use engine default CELL_SIZE


@dataclass(frozen=True)
class WaitCommand:
    ms: int


@dataclass(frozen=True)
class PrintBoardCommand:
    pass


@dataclass(frozen=True)
class JumpCommand:
    p: Point
    cell_size: int = 0  # 0 means use engine default CELL_SIZE
