from dataclasses import dataclass


@dataclass(frozen=True)
class ClickCommand:
    x: int
    y: int


@dataclass(frozen=True)
class WaitCommand:
    ms: int


@dataclass(frozen=True)
class PrintBoardCommand:
    pass
