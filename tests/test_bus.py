import logging
import pytest
from unittest.mock import MagicMock
from bus import Bus


@pytest.fixture
def bus():
    return Bus()


def test_subscribe_and_publish_calls_callback(bus):
    cb = MagicMock()
    bus.subscribe("move", cb)
    bus.publish("move", {"x": 1})
    cb.assert_called_once_with({"x": 1})


def test_publish_calls_all_subscribers(bus):
    cb1, cb2 = MagicMock(), MagicMock()
    bus.subscribe("move", cb1)
    bus.subscribe("move", cb2)
    bus.publish("move", {"x": 1})
    cb1.assert_called_once_with({"x": 1})
    cb2.assert_called_once_with({"x": 1})


def test_publish_no_subscribers_does_nothing(bus):
    bus.publish("ghost", {})  # must not raise


def test_publish_does_not_cross_event_names(bus):
    cb = MagicMock()
    bus.subscribe("move", cb)
    bus.publish("jump", {"x": 1})
    cb.assert_not_called()


def test_failing_callback_does_not_block_remaining_and_logs_warning(bus, caplog):
    bad = MagicMock(side_effect=RuntimeError("boom"))
    good = MagicMock()
    bus.subscribe("move", bad)
    bus.subscribe("move", good)

    with caplog.at_level(logging.WARNING, logger="bus"):
        bus.publish("move", {"x": 1})

    good.assert_called_once_with({"x": 1})
    assert "boom" in caplog.text
    assert any(r.levelname == "WARNING" for r in caplog.records)
