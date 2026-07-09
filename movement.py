from typing import Callable, Dict
from dataclasses import dataclass

from board import Board
from constants import PAWN_DOUBLE_STEP_ROWS

@dataclass(frozen=True)
class MoveContext:
    piece_type: str
    color: str
    fr: int
    fc: int
    tr: int
    tc: int
    board: Board


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sign(n: int) -> int:
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def path_clear(ctx: MoveContext) -> bool:
    """Return True if every cell *between* ctx.fr,ctx.fc and ctx.tr,ctx.tc is empty.

    Steps one cell at a time in the direction of travel.
    Does NOT check the destination itself.
    """
    dr = _sign(ctx.tr - ctx.fr)
    dc = _sign(ctx.tc - ctx.fc)
    r, c = ctx.fr + dr, ctx.fc + dc
    while (r, c) != (ctx.tr, ctx.tc):
        if ctx.board.get_token(r, c) != '.':
            return False
        r += dr
        c += dc
    return True


# ---------------------------------------------------------------------------
# Per-piece move validators
# Unified signature: (ctx: MoveContext) -> bool
# piece_type and color are unused by K/Q/R/B/N but required for interface
# consistency so all validators can be registered without wrappers.
# ---------------------------------------------------------------------------

def king_can_move(ctx: MoveContext) -> bool:
    return max(abs(ctx.tr - ctx.fr), abs(ctx.tc - ctx.fc)) == 1


def rook_can_move(ctx: MoveContext) -> bool:
    if ctx.fr != ctx.tr and ctx.fc != ctx.tc:
        return False
    return path_clear(ctx)


def bishop_can_move(ctx: MoveContext) -> bool:
    dr, dc = abs(ctx.tr - ctx.fr), abs(ctx.tc - ctx.fc)
    if dr == 0 or dr != dc:
        return False
    return path_clear(ctx)


def queen_can_move(ctx: MoveContext) -> bool:
    return (rook_can_move(ctx)
            or bishop_can_move(ctx))


def knight_can_move(ctx: MoveContext) -> bool:
    return sorted([abs(ctx.tr - ctx.fr), abs(ctx.tc - ctx.fc)]) == [1, 2]


def pawn_can_move(ctx: MoveContext) -> bool:
    """Pawn movement: forward-only advance to empty square, diagonal-only capture to occupied square.

    White moves toward row 0 (direction -1); black moves toward the last row (direction +1).
    The friendly-fire guard in ClickCommandHandler ensures the validator is only
    called when the destination is empty or an enemy, so the diagonal check only
    needs to confirm the square is not empty.
    """
    direction = -1 if ctx.color == 'w' else 1
    dr = ctx.tr - ctx.fr
    dc = abs(ctx.tc - ctx.fc)

    if dr == direction and dc == 0:
        return ctx.board.get_token(ctx.tr, ctx.tc) == '.'          # forward: must be empty

    if dr == direction and dc == 1:
        return ctx.board.get_token(ctx.tr, ctx.tc) != '.'          # diagonal: must be occupied (enemy)

    if dr == 2 * direction and dc == 0:
        start_row = ctx.board.rows - PAWN_DOUBLE_STEP_ROWS if ctx.color == 'w' else PAWN_DOUBLE_STEP_ROWS - 1
        return (ctx.fr == start_row
                and ctx.board.get_token(ctx.tr, ctx.tc) == '.'
                and path_clear(ctx))

    return False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ValidatorFn = Callable[[MoveContext], bool]


class MoveValidator:
    """Registry that maps piece type (single letter) to its move-legality function."""

    def __init__(self) -> None:
        self._validators: Dict[str, _ValidatorFn] = {}

    def register(self, piece_type: str, fn: _ValidatorFn) -> None:
        self._validators[piece_type] = fn

    def is_legal(self, ctx: MoveContext) -> bool:
        """Return True if moving the piece defined in ctx is legal."""
        fn = self._validators.get(ctx.piece_type)
        if fn is None:
            return False
        return fn(ctx)
