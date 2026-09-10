import logging
import pytest
from bus_factory import build_bus
from move_logger import log_move


# --- build_bus ---

def test_build_bus_returns_bus_with_move_made_subscriber():
    bus = build_bus()
    from unittest.mock import MagicMock
    cb = MagicMock()
    bus.subscribe("move_made", cb)
    bus.publish("move_made", {"raw": "wait 0", "state": None})
    cb.assert_called_once_with({"raw": "wait 0", "state": None})


def test_build_bus_subscribes_log_move(caplog):
    # Observable behavior: publishing move_made produces a log line — no patching
    bus = build_bus()
    with caplog.at_level(logging.INFO, logger="move_logger"):
        bus.publish("move_made", {"raw": "wait 0", "state": None})
    assert any("wait 0" in r.message for r in caplog.records)


# --- log_move ---

@pytest.mark.parametrize("raw,check", [
    ("click e2", lambda r: "click e2" in r.message),
    ("wait 100", lambda r: r.levelname == "INFO"),
])
def test_log_move_logs(raw, check, caplog):
    with caplog.at_level(logging.INFO, logger="move_logger"):
        log_move({"raw": raw, "state": None})
    assert any(check(r) for r in caplog.records)
