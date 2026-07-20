import pytest

from board import Board
from constants import JUMP_DURATION_MS
from exceptions import InvalidCommandArgumentError
from game_state import GameState
from handlers.jump import handle_jump, parse_jump
from models import BoardPosition


def _state(token_rows):
    board = Board(rows=len(token_rows), cols=len(token_rows[0]), grid=[list(r) for r in token_rows])
    return GameState(board=board)


# ---------------------------------------------------------------------------
# parse_jump
# ---------------------------------------------------------------------------

def test_parse_jump_valid():
    cmd = parse_jump(["jump", "50", "50"])
    assert cmd.p.x == 50 and cmd.p.y == 50


@pytest.mark.parametrize("args", [["jump", "abc", "50"], ["jump", "50"], ["jump"]])
def test_parse_jump_invalid_raises(args):
    with pytest.raises(InvalidCommandArgumentError):
        parse_jump(args)


# ---------------------------------------------------------------------------
# handle_jump
# ---------------------------------------------------------------------------

def test_handle_jump_schedules_airborne():
    state = _state([['wK', '.']])
    handle_jump(parse_jump(["jump", "50", "50"]), state)
    assert state.is_airborne(BoardPosition(0, 0))
    assert state.airborne[BoardPosition(0, 0)] == JUMP_DURATION_MS


def test_handle_jump_out_of_bounds_ignored():
    state = _state([['wK']])
    handle_jump(parse_jump(["jump", "9999", "9999"]), state)
    assert state.airborne == {}


def test_handle_jump_empty_cell_ignored():
    state = _state([['.']])
    handle_jump(parse_jump(["jump", "50", "50"]), state)
    assert state.airborne == {}
