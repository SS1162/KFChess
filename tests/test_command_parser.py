import pytest

from commands import WaitCommand
from handlers.wait import parse_wait
from parser import CommandParser


def test_registered_command_is_parsed():
    # Arrange
    cp = CommandParser()
    cp.register("wait", parse_wait)
    # Act / Assert
    assert cp.parse("wait 500") == WaitCommand(ms=500)


def test_unknown_keyword_returns_none():
    assert CommandParser().parse("resign") is None


def test_empty_line_returns_none():
    assert CommandParser().parse("   ") is None


@pytest.mark.parametrize("line", ["wait abc", "wait -5", "wait"])
def test_malformed_command_returns_none(line):
    # Arrange
    cp = CommandParser()
    cp.register("wait", parse_wait)
    # Act / Assert — CommandParser swallows CommandError and returns None
    assert cp.parse(line) is None
