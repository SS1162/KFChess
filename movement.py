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
# Unified signature: (piece_type, color, fr, fc, tr, tc, board) -> bool
# piece_type and color are unused by K/Q/R/B/N but required for interface
# consistency so all validators can be registered without wrappers.
# ---------------------------------------------------------------------------

def king_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    return max(abs(tr - fr), abs(tc - fc)) == 1


def rook_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    if fr != tr and fc != tc:
        return False
    return _path_clear(fr, fc, tr, tc, board)


def bishop_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    dr, dc = abs(tr - fr), abs(tc - fc)
    if dr == 0 or dr != dc:
        return False
    return _path_clear(fr, fc, tr, tc, board)


def queen_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    return (rook_can_move(piece_type, color, fr, fc, tr, tc, board)
            or bishop_can_move(piece_type, color, fr, fc, tr, tc, board))


def knight_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    return sorted([abs(tr - fr), abs(tc - fc)]) == [1, 2]


def pawn_can_move(piece_type: str, color: str, fr: int, fc: int, tr: int, tc: int, board: Board) -> bool:
    """Pawn movement: forward-only advance to empty square, diagonal-only capture to occupied square.

    White moves toward row 0 (direction -1); black moves toward the last row (direction +1).
    The friendly-fire guard in ClickCommandHandler ensures the validator is only
    called when the destination is empty or an enemy, so the diagonal check only
    needs to confirm the square is not empty.
    """
    direction = -1 if color == 'w' else 1
    dr = tr - fr
    dc = abs(tc - fc)

    if dr == direction and dc == 0:
        return board.get_token(tr, tc) == '.'          # forward: must be empty

    if dr == direction and dc == 1:
        return board.get_token(tr, tc) != '.'          # diagonal: must be occupied (enemy)

    return False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ValidatorFn = Callable[[str, str, int, int, int, int, Board], bool]


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
        return fn(piece_type, color, fr, fc, tr, tc, board)
