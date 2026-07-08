import pytest

from board import Board
from config import PIECE_COOLDOWN_MS
from game_state import GameState


def _state(token_rows):
    board = Board(rows=len(token_rows), cols=len(token_rows[0]), grid=[list(r) for r in token_rows])
    return GameState(board=board)


@pytest.mark.parametrize("clock, expiry, expected", [
    (0,    None, False),   # no cooldown entry → always available
    (500,  1000, True),    # clock before expiry → still cooling
    (1000, 1000, False),   # clock exactly at expiry → expired
    (1500, 1000, False),   # clock past expiry → available
])
def test_is_in_cooldown(clock, expiry, expected):
    # Arrange
    state = _state([['wK', '.']])
    state.clock_ms = clock
    if expiry is not None:
        state.cooldowns[(0, 0)] = expiry
    # Act / Assert
    assert state.is_in_cooldown(0, 0) == expected


def test_advance_clock_increments_clock_ms():
    state = _state([['.']])
    state.advance_clock(750)
    assert state.clock_ms == 750


def test_select_and_deselect_toggle_selection():
    # Arrange
    state = _state([['wK', '.']])
    # Act / Assert — select
    state.select(0, 0)
    assert state.selection == (0, 0)
    # Act / Assert — deselect
    state.deselect()
    assert state.selection is None


def test_apply_move_updates_board_and_stamps_cooldown():
    # Arrange
    state = _state([['wK', '.']])
    # Act
    state.apply_move(0, 0, 0, 1)
    # Assert — board mutated
    assert state.board.get_token(0, 0) == '.'
    assert state.board.get_token(0, 1) == 'wK'
    # Assert — cooldown stamped at destination, removed at source
    assert state.cooldowns.get((0, 1)) == PIECE_COOLDOWN_MS
    assert (0, 0) not in state.cooldowns
