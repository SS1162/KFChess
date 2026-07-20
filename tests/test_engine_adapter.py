import pytest
from board import Board
from game_state import GameState
from engine_adapter import run_single_command


def _state(grid):
    return GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))


# --- wait ---

def test_wait_advances_clock():
    state = _state([['.']])
    result = run_single_command(state, "wait 500")
    assert result.clock_ms == 500


def test_wait_returns_same_state_object():
    state = _state([['.']])
    assert run_single_command(state, "wait 100") is state


def test_wait_accumulates_across_calls():
    state = _state([['.']])
    run_single_command(state, "wait 200")
    run_single_command(state, "wait 300")
    assert state.clock_ms == 500


# --- click (select) ---

def test_click_selects_piece():
    # CELL_SIZE=100; click (50,50) → row=0, col=0
    state = _state([['wK']])
    run_single_command(state, "click 50 50")
    from models import BoardPosition
    assert state.selection == BoardPosition(0, 0)


def test_click_empty_square_no_selection():
    state = _state([['.']])
    run_single_command(state, "click 50 50")
    assert state.selection is None


# --- click (move scheduling) ---

def test_click_schedules_move():
    # 2-col board: wR at col0, empty at col1
    # click col0 to select, click col1 to move
    state = _state([['wR', '.']])
    run_single_command(state, "click 50 50")   # select (0,0)
    run_single_command(state, "click 150 50")  # move to (0,1)
    from models import BoardPosition
    assert BoardPosition(0, 0) in state.in_flight


# --- jump ---

def test_jump_marks_piece_airborne():
    state = _state([['wK']])
    run_single_command(state, "jump 50 50")
    from models import BoardPosition
    assert BoardPosition(0, 0) in state.airborne


def test_jump_empty_square_ignored():
    state = _state([['.']])
    run_single_command(state, "jump 50 50")
    assert len(state.airborne) == 0


# --- print (no state mutation) ---

def test_print_does_not_mutate_state(capsys):
    state = _state([['wK']])
    run_single_command(state, "print")
    assert state.clock_ms == 0
    assert state.selection is None


# --- unknown / malformed commands ---

def test_unknown_command_ignored():
    state = _state([['.']])
    result = run_single_command(state, "foobar 1 2 3")
    assert result.clock_ms == 0


def test_malformed_wait_ignored():
    state = _state([['.']])
    run_single_command(state, "wait notanumber")
    assert state.clock_ms == 0


def test_empty_string_ignored():
    state = _state([['.']])
    result = run_single_command(state, "")
    assert result is state
