import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from board import Board
from constants import JUMP_DURATION_MS, PAWN_PROMOTION_PIECE, TIME_PER_CELL_MS
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
    # Maps origin BoardPosition -> (to_row, to_col, arrival_ms)
    in_flight: Dict[BoardPosition, tuple] = field(default_factory=dict)
    # Maps BoardPosition -> land_at_ms for pieces currently airborne (jumped)
    airborne: Dict[BoardPosition, int] = field(default_factory=dict)
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
        return pos in self.in_flight

    def is_airborne(self, pos: BoardPosition) -> bool:
        """Return True if the piece at pos is currently airborne (jumped)."""
        return pos in self.airborne

    def is_destination_reserved(self, pos: BoardPosition) -> bool:
        """Return True if any currently in-flight piece is already heading to pos."""
        return any(tr == pos.row and tc == pos.col for tr, tc, _ in self.in_flight.values())

    def schedule_jump(self, row: int, col: int) -> None:
        """Register the piece at (row, col) as airborne for JUMP_DURATION_MS milliseconds.

        Guards:
        - Game must be PLAYING.
        - Cell must contain a piece (not empty).
        - Piece must not be in-flight.
        - Piece must not already be airborne.
        """
        if self.status != GameStatus.PLAYING:
            logger.info("schedule_jump ignored — game is not PLAYING (status=%s).", self.status)
            return
        pos = BoardPosition(row, col)
        token = self.board.get_token(row, col)
        if token == '.':
            logger.warning("schedule_jump ignored — no piece at (%d,%d).", row, col)
            return
        if self.is_in_flight(pos):
            logger.warning("schedule_jump ignored — piece at (%d,%d) is in-flight.", row, col)
            return
        if self.is_airborne(pos):
            logger.warning("schedule_jump ignored — piece at (%d,%d) is already airborne.", row, col)
            return
        land_at_ms = self.clock_ms + JUMP_DURATION_MS
        self.airborne[pos] = land_at_ms
        logger.info(
            "Piece %r at (%d,%d) is airborne; lands at %d ms.",
            token, row, col, land_at_ms,
        )

    def apply_landings(self) -> None:
        """Remove expired airborne entries (land_at_ms <= clock_ms)."""
        expired = [pos for pos, land_at_ms in self.airborne.items() if self.clock_ms >= land_at_ms]
        for pos in expired:
            del self.airborne[pos]
            logger.info("Airborne piece at (%d,%d) has landed.", pos.row, pos.col)

    def schedule_move(self, ctx: MoveContext) -> None:
        """Register a move as in-flight. Travel time scales with Chebyshev distance so
        that each cell of travel costs TIME_PER_CELL_MS milliseconds.
        The piece stays at its origin on the board until apply_arrivals() commits it.

        Ignored if the game is no longer in PLAYING status, if the piece is already
        in-flight, or if the piece is currently airborne.
        """
        if self.status != GameStatus.PLAYING:
            logger.info("schedule_move ignored — game is not PLAYING (status=%s).", self.status)
            return
        origin = BoardPosition(ctx.fr, ctx.fc)
        if self.is_in_flight(origin):
            logger.warning(
                "Piece at (%d,%d) is already in-flight — schedule_move ignored.",
                ctx.fr, ctx.fc,
            )
            return
        if self.is_airborne(origin):
            logger.warning(
                "Piece at (%d,%d) is airborne — schedule_move ignored.",
                ctx.fr, ctx.fc,
            )
            return
        distance = max(abs(ctx.tr - ctx.fr), abs(ctx.tc - ctx.fc))
        arrival_ms = self.clock_ms + distance * TIME_PER_CELL_MS
        self.in_flight[origin] = (ctx.tr, ctx.tc, arrival_ms)
        logger.info(
            "Move scheduled (%d,%d)\u2192(%d,%d); distance=%d cells, arrives at %d ms.",
            ctx.fr, ctx.fc, ctx.tr, ctx.tc, distance, arrival_ms,
        )

    def _cancel_blocked(self) -> None:
        """Cancel any in-flight piece whose path to its destination is now blocked."""
        blocked: List[BoardPosition] = [
            origin for origin, (tr, tc, _) in self.in_flight.items()
            if not path_clear(MoveContext(
                self.board.get_token(origin.row, origin.col)[1],
                self.board.get_token(origin.row, origin.col)[0],
                origin.row, origin.col, tr, tc, self.board,
            ))
        ]
        for origin in blocked:
            del self.in_flight[origin]
            logger.info("In-flight piece at (%d,%d) cancelled — path now blocked.", origin.row, origin.col)

    def _get_due_arrivals(self) -> List[BoardPosition]:
        """Return in-flight origins sorted earliest-first whose arrival_ms <= clock_ms."""
        return sorted(
            [origin for origin, (_, _, arrival_ms) in self.in_flight.items()
             if self.clock_ms >= arrival_ms],
            key=lambda origin: self.in_flight[origin][2],
        )

    def _cancel_captured_at_destination(self, dest: BoardPosition) -> None:
        """Step C: cancel all in-flight pieces invalidated by a piece landing on dest.

        Cancels:
        - a piece whose origin key is dest — captured while waiting to depart.
        - any piece heading *toward* dest — destination now occupied.
        """
        if dest in self.in_flight:
            del self.in_flight[dest]
            logger.info("In-flight piece at (%d,%d) cancelled — captured at its origin.", dest.row, dest.col)

        heading_there = [
            origin for origin, (tr, tc, _) in self.in_flight.items()
            if tr == dest.row and tc == dest.col
        ]
        for origin in heading_there:
            del self.in_flight[origin]
            logger.info(
                "In-flight piece at (%d,%d) cancelled — destination (%d,%d) now occupied.",
                origin.row, origin.col, dest.row, dest.col,
            )

    def _try_promote_pawn(self, row: int, col: int) -> None:
        """Promote the pawn at (row, col) if it has reached its last row."""
        token = self.board.get_token(row, col)
        if token[1] != 'P':
            return
        promotion_row = 0 if token[0] == 'w' else self.board.rows - 1
        if row == promotion_row:
            self.board.set_token(row, col, token[0] + PAWN_PROMOTION_PIECE)
            logger.info("Pawn at (%d,%d) promoted to %s.", row, col, PAWN_PROMOTION_PIECE)

    def _land_piece(self, origin: BoardPosition, dest: BoardPosition) -> None:
        """Commit a single arrived piece to the board, then run step C and D."""
        captured_token = self.board.get_token(dest.row, dest.col)
        self.board.apply_move(Move(origin.row, origin.col, dest.row, dest.col))
        logger.info("Piece arrived (%d,%d)\u2192(%d,%d).", origin.row, origin.col, dest.row, dest.col)
        self._try_promote_pawn(dest.row, dest.col)
        result = self.game_over_registry.resolve(captured_token)
        if result is not None:
            self.status = result
            logger.info("Game over — status set to %s.", self.status)
        self._cancel_captured_at_destination(dest)   # step C
        self._cancel_blocked()                        # step D

    def _try_air_capture(self, origin: BoardPosition, dest: BoardPosition) -> bool:
        """Check if an airborne enemy piece occupies dest and captures the arriving piece.

        If dest holds an airborne piece of the opposite color to the arriving piece:
        - The arriving piece is destroyed (never lands).
        - The airborne entry is immediately removed (jump ends on capture).
        - Game-over is checked against the arriving token.
        Returns True if an air capture occurred, False otherwise.
        """
        if dest not in self.airborne:
            return False
        arriving_token = self.board.get_token(origin.row, origin.col)
        resident_token = self.board.get_token(dest.row, dest.col)
        if arriving_token == '.' or resident_token == '.':
            return False
        if arriving_token[0] == resident_token[0]:
            return False  # same color — no air capture
        # Air capture: arriving enemy destroyed; airborne piece stays; jump ends immediately
        del self.airborne[dest]
        self.board.set_token(origin.row, origin.col, '.')  # remove arriving piece from its origin
        logger.info(
            "Air capture: airborne %r at (%d,%d) captured arriving %r from (%d,%d). Jump ended.",
            resident_token, dest.row, dest.col, arriving_token, origin.row, origin.col,
        )
        result = self.game_over_registry.resolve(arriving_token)
        if result is not None:
            self.status = result
            logger.info("Game over via air capture — status set to %s.", self.status)
        return True

    def apply_arrivals(self) -> None:
        """Commit every due in-flight move to the board, earliest-first.

        Before landing, check for air capture: if an airborne enemy occupies the
        destination, the airborne piece captures the arriving piece instead.
        """
        for origin in self._get_due_arrivals():
            if origin not in self.in_flight:
                continue  # cancelled by a previous arrival this tick
            tr, tc, _ = self.in_flight.pop(origin)
            dest = BoardPosition(tr, tc)
            if self._try_air_capture(origin, dest):
                continue  # air capture handled — skip normal landing
            self._land_piece(origin, dest)

    def apply_move(self, move: Move) -> None:
        """Instantly moves a piece, captures any occupant."""
        self.board.apply_move(move)
        logger.info(
            "Move applied (%d,%d)\u2192(%d,%d).",
            move.fr, move.fc, move.tr, move.tc,
        )
