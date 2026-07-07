from dataclasses import dataclass
from typing import List


@dataclass
class Board:
    """Immutable model that holds the validated board state."""
    rows: int
    cols: int
    grid: List[List[str]]

    def __str__(self) -> str:
        return '\n'.join(' '.join(row) for row in self.grid)
