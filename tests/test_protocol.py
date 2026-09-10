import pytest
from board import Board
from game_state import GameState
from game_status import GameStatus
from protocol import (
    IncomingCommand, ProtocolError,
    parse_incoming, serialize_state,
)


def _state(grid, status=GameStatus.PLAYING):
    s = GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))
    s.status = status
    return s


# --- parse_incoming happy path ---

@pytest.mark.parametrize("raw", [
    "wait 500",
    "click 50 50",
    "  jump 10 20  ",
])
def test_parse_incoming_valid(raw):
    result = parse_incoming({"type": "command", "raw": raw})
    assert isinstance(result, IncomingCommand)
    assert result.raw == raw
    assert result.type == "command"


# --- parse_incoming unhappy path ---

@pytest.mark.parametrize("bad", [
    {},
    {"type": "command", "raw": ""},
    {"type": "command", "raw": "   "},
    {"type": "command", "raw": 123},
    {"type": "join", "raw": "wait 0"},
    "wait 0",
    None,
])
def test_parse_incoming_invalid_raises(bad):
    with pytest.raises(ProtocolError):
        parse_incoming(bad)


# --- serialize_state ---

def test_serialize_state_values():
    result = serialize_state(_state([["wK", "bK"]], status=GameStatus.WHITE_WON))
    assert set(result.keys()) == {"type", "board", "status"}
    assert result["type"] == "state"
    assert result["board"] == [["wK", "bK"]]
    assert result["status"] == "WHITE_WON"


@pytest.mark.parametrize("status", [
    GameStatus.PLAYING,
    GameStatus.WHITE_WON,
    GameStatus.BLACK_WON,
    GameStatus.DRAW,
])
def test_serialize_state_status_name(status):
    result = serialize_state(_state([["."]],  status=status))
    assert result["status"] == status.name


def test_serialize_state_board_is_copy():
    grid = [["wK", "."]]
    state = _state(grid)
    result = serialize_state(state)
    result["board"][0][0] = "MUTATED"
    assert state.board.get_token(0, 0) == "wK"
