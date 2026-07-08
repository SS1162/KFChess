import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from board import Board
from constants import TIME_PER_CELL_MS
from models import Move
from movement import MoveContext

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Mutable engine state: board position, virtual clock, selection, piece cooldowns, and in-flight moves."""
    board: Board
    clock_ms: int = 0
    selection: Optional[Tuple[int, int]] = None
    # Maps (from_row, from_col) -> (to_row, to_col, arrival_ms)
    in_flight: Dict[Tuple[int, int], Tuple[int, int, int]] = field(default_factory=dict)

    def advance_clock(self, ms: int) -> None:
        """Advance the virtual game clock by the given number of milliseconds."""
        self.clock_ms += ms

    def select(self, row: int, col: int) -> None:
        """Set the active selection to the piece at (row, col)."""
        self.selection = (row, col)

    def deselect(self) -> None:
        """Clear the active selection."""
        self.selection = None

    def is_in_flight(self, row: int, col: int) -> bool:
        """Return True if the piece at (row, col) is currently in-flight."""
        return (row, col) in self.in_flight

    def is_destination_reserved(self, to_row: int, to_col: int) -> bool:
        """Return True if any currently in-flight piece is already heading to (to_row, to_col)."""
        return any(tr == to_row and tc == to_col for tr, tc, _ in self.in_flight.values())

    def schedule_move(self, ctx: MoveContext) -> None:
        """Register a move as in-flight. Travel time scales with Chebyshev distance so
        that each cell of travel costs TIME_PER_CELL_MS milliseconds.
        The piece stays at its origin on the board until apply_arrivals() commits it.

        If the piece at (ctx.fr, ctx.fc) is already in-flight, the request is
        silently ignored — no state is mutated.
        """
        if self.is_in_flight(ctx.fr, ctx.fc):
            logger.warning(
                "Piece at (%d,%d) is already in-flight — schedule_move ignored.",
                ctx.fr, ctx.fc,
            )
            return
        distance = max(abs(ctx.tr - ctx.fr), abs(ctx.tc - ctx.fc))
        arrival_ms = self.clock_ms + distance * TIME_PER_CELL_MS
        self.in_flight[(ctx.fr, ctx.fc)] = (ctx.tr, ctx.tc, arrival_ms)
        logger.info(
            "Move scheduled (%d,%d)\u2192(%d,%d); distance=%d cells, arrives at %d ms.",
            ctx.fr, ctx.fc, ctx.tr, ctx.tc, distance, arrival_ms,
        )

    def apply_arrivals(self) -> None:
        """Commit every in-flight move whose arrival_ms <= clock_ms to the board."""
        arrived = [
            (fr, fc) for (fr, fc), (_, _, arrival_ms) in self.in_flight.items()
            if self.clock_ms >= arrival_ms
        ]
        for fr, fc in arrived:
            to_row, to_col, arrival_ms = self.in_flight.pop((fr, fc))
            self.board.apply_move(Move(fr, fc, to_row, to_col))
            logger.info(
                "Piece arrived (%d,%d)\u2192(%d,%d); ready to move immediately.",
                fr, fc, to_row, to_col,
            )

    def apply_move(self, move: Move) -> None:
        """Instantly moves a piece, captures any occupant."""
        self.board.apply_move(move)
        logger.info(
            "Move applied (%d,%d)\u2192(%d,%d).",
            move.fr, move.fc, move.tr, move.tc,
        )
