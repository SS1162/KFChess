import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from board import Board
from config import PIECE_COOLDOWN_MS

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Mutable engine state: board position, virtual clock, selection, and piece cooldowns."""
    board: Board
    clock_ms: int = 0
    selection: Optional[Tuple[int, int]] = None
    cooldowns: Dict[Tuple[int, int], int] = field(default_factory=dict)

    def is_in_cooldown(self, row: int, col: int) -> bool:
        """Returns True if the piece at (row, col) cannot yet move."""
        return self.cooldowns.get((row, col), 0) > self.clock_ms

    def advance_clock(self, ms: int) -> None:
        """Advance the virtual game clock by the given number of milliseconds."""
        self.clock_ms += ms

    def select(self, row: int, col: int) -> None:
        """Set the active selection to the piece at (row, col)."""
        self.selection = (row, col)

    def deselect(self) -> None:
        """Clear the active selection."""
        self.selection = None

    def apply_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> None:
        """Instantly moves a piece, captures any occupant, and starts its cooldown."""
        self.board.apply_move(from_row, from_col, to_row, to_col)
        self.cooldowns.pop((from_row, from_col), None)
        self.cooldowns[(to_row, to_col)] = self.clock_ms + PIECE_COOLDOWN_MS
        logger.info(
            "Move applied (%d,%d)\u2192(%d,%d); cooldown until %d ms.",
            from_row, from_col, to_row, to_col, self.cooldowns[(to_row, to_col)],
        )
