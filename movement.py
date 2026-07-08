from typing import Callable, Dict

from board import Board


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sign(n: int) -> int:
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def _path_clear(fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    """Return True if every cell *between* (fr,fc) and (tr,tc) is empty.

    Steps one cell at a time in the direction of travel.
    Does NOT check the destination itself.
    """
    dr = _sign(tr - fr)
    dc = _sign(tc - fc)
    r, c = fr + dr, fc + dc
    while (r, c) != (tr, tc):
        if board.get_token(r, c) != '.':
            return False
        r += dr
        c += dc
    return True


# ---------------------------------------------------------------------------
# Per-piece move validators
# Signature: (fr, fc, tr, tc, board, color) -> bool
# color is unused by K/Q/R/B/N but present for Pawn compatibility later.
# ---------------------------------------------------------------------------

def king_can_move(fr: int, fc: int, tr: int, tc: int, board: Board, color: str) -> bool:
    return max(abs(tr - fr), abs(tc - fc)) == 1


def rook_can_move(fr: int, fc: int, tr: int, tc: int, board: Board, color: str) -> bool:
    if fr != tr and fc != tc:
        return False
    return _path_clear(fr, fc, tr, tc, board)


def bishop_can_move(fr: int, fc: int, tr: int, tc: int, board: Board, color: str) -> bool:
    dr, dc = abs(tr - fr), abs(tc - fc)
    if dr == 0 or dr != dc:
        return False
    return _path_clear(fr, fc, tr, tc, board)


def queen_can_move(fr: int, fc: int, tr: int, tc: int, board: Board, color: str) -> bool:
    return (rook_can_move(fr, fc, tr, tc, board, color)
            or bishop_can_move(fr, fc, tr, tc, board, color))


def knight_can_move(fr: int, fc: int, tr: int, tc: int, board: Board, color: str) -> bool:
    return sorted([abs(tr - fr), abs(tc - fc)]) == [1, 2]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ValidatorFn = Callable[[int, int, int, int, Board, str], bool]


class MoveValidator:
    """Registry that maps piece type (single letter) to its move-legality function."""

    def __init__(self) -> None:
        self._validators: Dict[str, _ValidatorFn] = {}

    def register(self, piece_type: str, fn: _ValidatorFn) -> None:
        self._validators[piece_type] = fn

    def is_legal(
        self,
        piece_type: str,
        color: str,
        fr: int,
        fc: int,
        tr: int,
        tc: int,
        board: Board,
    ) -> bool:
        """Return True if moving the piece of *piece_type*/*color* from (fr,fc) to (tr,tc) is legal."""
        fn = self._validators.get(piece_type)
        if fn is None:
            return False
        return fn(fr, fc, tr, tc, board, color)
