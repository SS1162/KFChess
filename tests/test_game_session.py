import logging
import pytest
from unittest.mock import MagicMock, patch
from board import Board
from bus import Bus
from game_state import GameState
from game_session import GameSession


def _session():
    state = GameState(board=Board(rows=1, cols=1, grid=[["wK"]]))
    return GameSession(state, Bus())


# --- Happy path ---

def test_apply_command_returns_state_dict():
    result = _session().apply_command({"type": "command", "raw": "wait 0"})
    assert result["type"] == "state"
    assert "board" in result
    assert "status" in result


def test_apply_command_mutates_state():
    session = _session()
    session.apply_command({"type": "command", "raw": "wait 500"})
    assert session.state.clock_ms == 500


# --- ProtocolError branch ---

@pytest.mark.parametrize("bad", [
    {},
    {"type": "command", "raw": ""},
    {"type": "join", "raw": "wait 0"},
    "wait 0",
    None,
])
def test_apply_command_invalid_raw_returns_error(bad, caplog):
    bus = MagicMock()
    state = GameState(board=Board(rows=1, cols=1, grid=[["wK"]]))
    session = GameSession(state, bus)
    with caplog.at_level(logging.WARNING, logger="game_session"):
        result = session.apply_command(bad)
    assert result["type"] == "error"
    assert result["reason"]
    assert any("Invalid incoming message" in r.message for r in caplog.records)
    bus.publish.assert_not_called()


# --- Engine exception branch ---

def test_apply_command_engine_exception_returns_error(caplog):
    bus = MagicMock()
    state = GameState(board=Board(rows=1, cols=1, grid=[["wK"]]))
    session = GameSession(state, bus)
    with patch("engine_adapter.run_single_command", side_effect=RuntimeError("boom")):
        with caplog.at_level(logging.WARNING, logger="game_session"):
            result = session.apply_command({"type": "command", "raw": "wait 100"})
    assert result["type"] == "error"
    assert "boom" in result["reason"]
    assert any("Engine error" in r.message for r in caplog.records)
    bus.publish.assert_not_called()


# --- Bus publishing ---

def test_apply_command_publishes_move_made_on_success():
    bus = MagicMock()
    state = GameState(board=Board(rows=1, cols=1, grid=[["wK"]]))
    session = GameSession(state, bus)
    session.apply_command({"type": "command", "raw": "wait 0"})
    bus.publish.assert_called_once_with("move_made", {"raw": "wait 0", "state": state})
