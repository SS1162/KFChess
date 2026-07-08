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

    def apply_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> None:
        """Move token to destination (capturing any occupant) and clear the source cell."""
        self.grid[to_row][to_col] = self.grid[from_row][from_col]
        self.grid[from_row][from_col] = '.'
