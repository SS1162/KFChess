import pytest
from board import Board
from game_state import GameState
from models import BoardPosition
from engine_adapter import run_single_command


def _state(grid):
    return GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))


# --- Happy path ---

@pytest.mark.parametrize("cmd, expected_ms", [
    ("wait 500", 500),
    ("wait 0",   0),
])
def test_wait_advances_clock(cmd, expected_ms):
    state = _state([['.']])
    result = run_single_command(state, cmd)
    assert result.clock_ms == expected_ms
    assert result is state


def test_click_selects_then_schedules_move():
    # CELL_SIZE=100; (50,50)→(0,0), (150,50)→(0,1)
    state = _state([['wR', '.']])

    run_single_command(state, "click 50 50")
    assert state.selection == BoardPosition(0, 0)

    run_single_command(state, "click 150 50")
    assert state.selection is None
    assert BoardPosition(0, 0) in state.in_flight


def test_jump_marks_piece_airborne():
    state = _state([['wK']])
    run_single_command(state, "jump 50 50")
    assert BoardPosition(0, 0) in state.airborne


def test_print_no_state_mutation(capsys):
    state = _state([['wK']])
    run_single_command(state, "print")
    assert state.clock_ms == 0
    assert state.selection is None


# --- Unhappy path ---

@pytest.mark.parametrize("cmd", [
    "foobar 1 2",   # unknown keyword
    "wait notanum", # malformed argument
    "",             # empty string
])
def test_invalid_commands_ignored(cmd):
    state = _state([['.']])
    result = run_single_command(state, cmd)
    assert result.clock_ms == 0
    assert result is state


@pytest.mark.parametrize("cmd", [
    "click 50 50",  # click on empty square → no selection
    "jump 50 50",   # jump on empty square → no airborne
])
def test_commands_on_empty_square_ignored(cmd):
    state = _state([['.']])
    run_single_command(state, cmd)
    assert state.selection is None
    assert len(state.airborne) == 0
