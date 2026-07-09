import pytest

from board import Board
from movement import (MoveContext, MoveValidator, bishop_can_move, king_can_move,
                      knight_can_move, pawn_can_move, queen_can_move,
                      rook_can_move)


def _board(token_rows):
    return Board(rows=len(token_rows), cols=len(token_rows[0]), grid=[list(r) for r in token_rows])


# ---------------------------------------------------------------------------
# King
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tr,tc", [
    (0, 1), (1, 0), (1, 1),  # right, down, diagonal
    (0, -1), (-1, 0),        # left, up (handled by board bounds in real game)
])
def test_king_legal_moves(tr, tc):
    board = _board([['.' * 3] * 3])  # board shape irrelevant; king has no path check
    assert king_can_move(MoveContext('K', 'w', 0, 0, tr, tc, board)) is True


@pytest.mark.parametrize("tr,tc", [
    (0, 2),   # two steps horizontally
    (2, 0),   # two steps vertically
    (2, 2),   # two steps diagonally
    (0, 0),   # no movement (same cell)
])
def test_king_illegal_moves(tr, tc):
    board = _board([['wK', '.', '.'], ['.', '.', '.'], ['.', '.', '.']])
    assert king_can_move(MoveContext('K', 'w', 0, 0, tr, tc, board)) is False


# ---------------------------------------------------------------------------
# Rook
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tr,tc", [(0, 3), (3, 0)])
def test_rook_legal_moves_on_clear_path(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert rook_can_move(MoveContext('R', 'w', 0, 0, tr, tc, board)) is True


@pytest.mark.parametrize("tr,tc", [(1, 1), (2, 2)])
def test_rook_cannot_move_diagonally(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert rook_can_move(MoveContext('R', 'w', 0, 0, tr, tc, board)) is False


def test_rook_blocked_by_intermediate_piece():
    # wR . bP .  — rook at col 0 cannot jump over bP at col 2 to reach col 3
    board = _board([['wR', '.', 'bP', '.']])
    assert rook_can_move(MoveContext('R', 'w', 0, 0, 0, 3, board)) is False


def test_rook_can_reach_blocker_cell_itself():
    # The destination itself is not an intermediate cell — path check stops before it
    board = _board([['wR', '.', 'bP', '.']])
    assert rook_can_move(MoveContext('R', 'w', 0, 0, 0, 2, board)) is True


# ---------------------------------------------------------------------------
# Bishop
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tr,tc", [(2, 2), (3, 3)])
def test_bishop_legal_diagonal_moves(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert bishop_can_move(MoveContext('B', 'w', 0, 0, tr, tc, board)) is True


@pytest.mark.parametrize("tr,tc", [(0, 2), (2, 0), (1, 2)])
def test_bishop_cannot_move_non_diagonally(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert bishop_can_move(MoveContext('B', 'w', 0, 0, tr, tc, board)) is False


def test_bishop_blocked_by_intermediate_piece():
    # Diagonal: (0,0) → (2,2), piece at (1,1) blocks
    board = _board([['wB', '.', '.'], ['.', 'bP', '.'], ['.', '.', '.']])
    assert bishop_can_move(MoveContext('B', 'w', 0, 0, 2, 2, board)) is False


# ---------------------------------------------------------------------------
# Queen (delegates — one legal and one illegal case each direction is enough)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tr,tc", [(0, 3), (3, 0), (3, 3)])
def test_queen_legal_moves(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert queen_can_move(MoveContext('Q', 'w', 0, 0, tr, tc, board)) is True


@pytest.mark.parametrize("tr,tc", [(1, 2), (2, 1)])
def test_queen_illegal_moves(tr, tc):
    board = _board([['.'] * 4, ['.'] * 4, ['.'] * 4, ['.'] * 4])
    assert queen_can_move(MoveContext('Q', 'w', 0, 0, tr, tc, board)) is False


# ---------------------------------------------------------------------------
# Knight
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tr,tc", [(1, 2), (2, 1), (-1, 2), (-2, 1)])
def test_knight_legal_moves(tr, tc):
    board = _board([['.'] * 5, ['.'] * 5, ['.'] * 5])  # shape irrelevant; knight jumps
    assert knight_can_move(MoveContext('N', 'w', 0, 0, tr, tc, board)) is True


@pytest.mark.parametrize("tr,tc", [(0, 1), (1, 1), (2, 2), (0, 3)])
def test_knight_illegal_moves(tr, tc):
    board = _board([['.'] * 5, ['.'] * 5, ['.'] * 5])
    assert knight_can_move(MoveContext('N', 'w', 0, 0, tr, tc, board)) is False


def test_knight_jumps_over_pieces():
    # Pieces between source and destination do not block a knight
    board = _board([['wN', 'bP', '.', '.'], ['bP', '.', '.', '.'], ['.', '.', '.', '.']])
    assert knight_can_move(MoveContext('N', 'w', 0, 0, 1, 2, board)) is True


# ---------------------------------------------------------------------------
# Pawn
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("color,fr,fc,tr,tc,token_rows", [
    # white forward to empty square
    ('w', 1, 0, 0, 0, [['.',  '.'], ['wP', '.']]),
    # white diagonal capture to occupied square
    ('w', 1, 0, 0, 1, [['.', 'bR'], ['wP', '.']]),
    # black forward to empty square
    ('b', 0, 0, 1, 0, [['bP', '.'], ['.',  '.']]),
    # black diagonal capture to occupied square
    ('b', 0, 0, 1, 1, [['bP', '.'], ['.',  'wQ']]),
    # white two-step from start row (clear path)
    ('w', 7, 0, 5, 0, [['.']*1]*8),
    # black two-step from start row (clear path)
    ('b', 0, 0, 2, 0, [['.']*1]*8),
])
def test_pawn_legal_moves(color, fr, fc, tr, tc, token_rows):
    board = _board(token_rows)
    assert pawn_can_move(MoveContext('P', color, fr, fc, tr, tc, board)) is True


@pytest.mark.parametrize("color,fr,fc,tr,tc,token_rows", [
    # forward to occupied square (blocked)
    ('w', 1, 0, 0, 0, [['bQ', '.'], ['wP', '.']]),
    # diagonal to empty square (no capture target)
    ('w', 1, 0, 0, 1, [['.',  '.'], ['wP', '.']]),
    # backward move
    ('w', 0, 0, 1, 0, [['wP', '.'], ['.',  '.']]),
    # two-step from non-start row
    ('w', 3, 0, 1, 0, [['.']*1]*8),
    # two-step blocked by intermediate piece
    ('w', 7, 0, 5, 0, [['.'], ['.'], ['.'], ['.'], ['.'], ['.'], ['bP'], ['.']]),
    # black moving in wrong direction
    ('b', 1, 0, 0, 0, [['.',  '.'], ['bP', '.']]),
])
def test_pawn_illegal_moves(color, fr, fc, tr, tc, token_rows):
    board = _board(token_rows)
    assert pawn_can_move(MoveContext('P', color, fr, fc, tr, tc, board)) is False


# ---------------------------------------------------------------------------
# MoveValidator — registry dispatch
# ---------------------------------------------------------------------------

def test_validator_dispatches_correct_function():
    mv = MoveValidator()
    mv.register('K', king_can_move)
    board = _board([['.'] * 3, ['.'] * 3, ['.'] * 3])
    assert mv.is_legal(MoveContext('K', 'w', 0, 0, 0, 1, board)) is True


def test_validator_returns_false_for_unknown_piece():
    mv = MoveValidator()
    board = _board([['.'] * 3])
    assert mv.is_legal(MoveContext('X', 'w', 0, 0, 0, 1, board)) is False
