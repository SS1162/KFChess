import pytest
from unittest.mock import MagicMock, patch
from board import Board
from game_state import GameState
from game_status import GameStatus
from game_session import GameSession


def _session():
    state = GameState(board=Board(rows=1, cols=1, grid=[["wK"]]))
    return GameSession(state)


# --- Happy path ---

def test_apply_command_returns_state_dict():
    result = _session().apply_command("wait 0")
    assert result["type"] == "state"
    assert "board" in result
    assert "status" in result


def test_apply_command_mutates_state():
    session = _session()
    session.apply_command("wait 500")
    assert session.state.clock_ms == 500


# --- ProtocolError branch ---

@pytest.mark.parametrize("bad", ["", "   ", 123, None])
def test_apply_command_invalid_raw_returns_error(bad):
    result = _session().apply_command(bad)
    assert result["type"] == "error"
    assert result["reason"]


def test_apply_command_protocol_error_logs_warning(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="game_session"):
        _session().apply_command("")
    assert any("Invalid incoming message" in r.message for r in caplog.records)


# --- Engine exception branch ---

def test_apply_command_engine_exception_returns_error():
    session = _session()
    with patch("engine_adapter.run_single_command", side_effect=RuntimeError("boom")):
        result = session.apply_command("wait 100")
    assert result["type"] == "error"
    assert "boom" in result["reason"]


def test_apply_command_engine_exception_logs_warning(caplog):
    import logging
    session = _session()
    with patch("engine_adapter.run_single_command", side_effect=RuntimeError("boom")):
        with caplog.at_level(logging.WARNING, logger="game_session"):
            session.apply_command("wait 100")
    assert any("Engine error" in r.message for r in caplog.records)
