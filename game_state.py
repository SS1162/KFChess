import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from board import Board
from constants import TIME_PER_CELL_MS
from game_status import GameOverRegistry, GameStatus, default_registry
from models import BoardPosition, Move
from movement import MoveContext, path_clear

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Mutable engine state: board position, virtual clock, selection, piece cooldowns, and in-flight moves."""
    board: Board
    clock_ms: int = 0
    selection: Optional[BoardPosition] = None
    # Maps (from_row, from_col) -> (to_row, to_col, arrival_ms)
    in_flight: Dict[Tuple[int, int], Tuple[int, int, int]] = field(default_factory=dict)
    status: GameStatus = field(default=GameStatus.PLAYING)
    game_over_registry: GameOverRegistry = field(default_factory=lambda: default_registry)

    def advance_clock(self, ms: int) -> None:
        """Advance the virtual game clock by the given number of milliseconds."""
        self.clock_ms += ms

    def select(self, pos: BoardPosition) -> None:
        """Set the active selection to the piece at pos."""
        self.selection = pos

    def deselect(self) -> None:
        """Clear the active selection."""
        self.selection = None

    def is_in_flight(self, pos: BoardPosition) -> bool:
        """Return True if the piece at pos is currently in-flight."""
        return (pos.row, pos.col) in self.in_flight

    def is_destination_reserved(self, pos: BoardPosition) -> bool:
        """Return True if any currently in-flight piece is already heading to pos."""
        return any(tr == pos.row and tc == pos.col for tr, tc, _ in self.in_flight.values())

    def schedule_move(self, ctx: MoveContext) -> None:
        """Register a move as in-flight. Travel time scales with Chebyshev distance so
        that each cell of travel costs TIME_PER_CELL_MS milliseconds.
        The piece stays at its origin on the board until apply_arrivals() commits it.

        Ignored if the game is no longer in PLAYING status, or if the piece at
        (ctx.fr, ctx.fc) is already in-flight.
        """
        if self.status != GameStatus.PLAYING:
            logger.info("schedule_move ignored — game is not PLAYING (status=%s).", self.status)
            return
        if self.is_in_flight(BoardPosition(ctx.fr, ctx.fc)):
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

    def _cancel_blocked(self) -> None:
        """Cancel any in-flight piece whose path to its destination is now blocked."""
        blocked = [
            (fr, fc) for (fr, fc), (tr, tc, _) in self.in_flight.items()
            if not path_clear(MoveContext(
                self.board.get_token(fr, fc)[1], self.board.get_token(fr, fc)[0],
                fr, fc, tr, tc, self.board,
            ))
        ]
        for fr, fc in blocked:
            self.in_flight.pop((fr, fc))
            logger.info("In-flight piece at (%d,%d) cancelled — path now blocked.", fr, fc)

    def _get_due_arrivals(self) -> list:
        """Return in-flight origins sorted earliest-first whose arrival_ms <= clock_ms."""
        return sorted(
            [(fr, fc) for (fr, fc), (_, _, arrival_ms) in self.in_flight.items()
             if self.clock_ms >= arrival_ms],
            key=lambda pos: self.in_flight[pos][2],
        )

    def _cancel_captured_at_destination(self, to_row: int, to_col: int) -> None:
        """Step C: cancel all in-flight pieces invalidated by a piece landing on (to_row, to_col).

        Cancels:
        - a piece whose origin key is (to_row, to_col) — captured while waiting to depart.
        - any piece heading *toward* (to_row, to_col) — destination now occupied.
        """
        if (to_row, to_col) in self.in_flight:
            self.in_flight.pop((to_row, to_col))
            logger.info("In-flight piece at (%d,%d) cancelled — captured at its origin.", to_row, to_col)

        heading_there = [
            (fr, fc) for (fr, fc), (tr, tc, _) in self.in_flight.items()
            if tr == to_row and tc == to_col
        ]
        for fr, fc in heading_there:
            self.in_flight.pop((fr, fc))
            logger.info("In-flight piece at (%d,%d) cancelled — destination (%d,%d) now occupied.", fr, fc, to_row, to_col)

    def _land_piece(self, fr: int, fc: int, to_row: int, to_col: int) -> None:
        """Commit a single arrived piece to the board, then run step C and D."""
        captured_token = self.board.get_token(to_row, to_col)
        self.board.apply_move(Move(fr, fc, to_row, to_col))
        logger.info("Piece arrived (%d,%d)\u2192(%d,%d).", fr, fc, to_row, to_col)
        result = self.game_over_registry.resolve(captured_token)
        if result is not None:
            self.status = result
            logger.info("Game over — status set to %s.", self.status)
        self._cancel_captured_at_destination(to_row, to_col)  # step C
        self._cancel_blocked()                                  # step D

    def apply_arrivals(self) -> None:
        """Commit every due in-flight move to the board, earliest-first."""
        for fr, fc in self._get_due_arrivals():
            if (fr, fc) not in self.in_flight:
                continue  # cancelled by a previous arrival this tick
            to_row, to_col, _ = self.in_flight.pop((fr, fc))
            self._land_piece(fr, fc, to_row, to_col)

    def apply_move(self, move: Move) -> None:
        """Instantly moves a piece, captures any occupant."""
        self.board.apply_move(move)
        logger.info(
            "Move applied (%d,%d)\u2192(%d,%d).",
            move.fr, move.fc, move.tr, move.tc,
        )
