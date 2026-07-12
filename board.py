from typing import List

from models import Move


from dataclasses import dataclass

@dataclass
class Board:
    """Immutable model that holds the validated board state."""
    rows: int
    cols: int
    grid: List[List[str]]

    def __str__(self) -> str:
        return '\n'.join(' '.join(row) for row in self.grid)

    def get_token(self, row: int, col: int) -> str:
        """Return the token at (row, col) without exposing the internal grid."""
        return self.grid[row][col]

    def apply_move(self, move: Move) -> None:
        """Move token to destination (capturing any occupant) and clear the source cell."""
        self.grid[move.tr][move.tc] = self.grid[move.fr][move.fc]
        self.grid[move.fr][move.fc] = '.'

    def set_token(self, row: int, col: int, token: str) -> None:
        """Overwrite the token at (row, col)."""
        self.grid[row][col] = token
