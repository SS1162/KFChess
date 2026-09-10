import pytest
from matchmaker import Matchmaker


@pytest.fixture
def mm():
    return Matchmaker()


def test_find_match_returns_none_when_no_candidates(mm):
    assert mm.find_match("p1", 1000) is None


def test_find_match_adds_player_to_waiting(mm):
    mm.find_match("p1", 1000)
    assert mm.is_waiting("p1")


@pytest.mark.parametrize("elo_diff", [0, 100])
def test_find_match_returns_opponent_within_range(mm, elo_diff):
    mm.find_match("p1", 1000)
    result = mm.find_match("p2", 1000 + elo_diff)
    assert result == "p1"


def test_find_match_removes_matched_player_from_waiting(mm):
    mm.find_match("p1", 1000)
    mm.find_match("p2", 1000)
    assert not mm.is_waiting("p1")


def test_find_match_rejects_opponent_outside_range(mm):
    mm.find_match("p1", 1000)
    assert mm.find_match("p2", 1101) is None


def test_find_match_skips_self(mm):
    mm.find_match("p1", 1000)
    assert mm.find_match("p1", 1000) is None


def test_remove_eliminates_waiting_player(mm):
    mm.find_match("p1", 1000)
    mm.remove("p1")
    assert not mm.is_waiting("p1")


def test_remove_nonexistent_player_is_noop(mm):
    mm.remove("ghost")  # should not raise
