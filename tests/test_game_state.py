import pytest

from board import Board
from constants import TIME_PER_CELL_MS
from game_state import GameState
from game_status import GameStatus
from models import BoardPosition, Move
from movement import MoveContext


def _state(token_rows):
    board = Board(rows=len(token_rows), cols=len(token_rows[0]), grid=[list(r) for r in token_rows])
    return GameState(board=board)



def test_advance_clock_increments_clock_ms():
    state = _state([['.']])
    state.advance_clock(750)
    assert state.clock_ms == 750


def test_select_and_deselect_toggle_selection():
    # Arrange
    state = _state([['wK', '.']])
    # Act / Assert — select
    state.select(BoardPosition(0, 0))
    assert state.selection == BoardPosition(0, 0)
    # Act / Assert — deselect
    state.deselect()
    assert state.selection is None


def test_apply_move_updates_board():
    # Arrange
    state = _state([['wK', '.']])
    # Act
    state.apply_move(Move(0, 0, 0, 1))
    # Assert — board mutated
    assert state.board.get_token(0, 0) == '.'
    assert state.board.get_token(0, 1) == 'wK'


# ---------------------------------------------------------------------------
# schedule_move
# ---------------------------------------------------------------------------

def test_schedule_move_piece_stays_at_origin():
    # Arrange
    state = _state([['wK', '.']])
    # Act
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    # Assert — board untouched; piece remains visible at origin
    assert state.board.get_token(0, 0) == 'wK'
    assert state.board.get_token(0, 1) == '.'


def test_schedule_move_ignores_already_in_flight():
    # Arrange — piece already in-flight to (0, 1)
    state = _state([['wK', '.', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    original_entry = state.in_flight[(0, 0)]
    # Act — attempt to redirect to (0, 2) while still in-flight
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 2, state.board))
    # Assert — in_flight entry is unchanged; redirect was silently ignored
    assert state.in_flight[(0, 0)] == original_entry


# ---------------------------------------------------------------------------
# apply_arrivals
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("clock_ms, origin, dest", [
    (1 * TIME_PER_CELL_MS - 1, 'wK', '.'),  # just before arrival (1-cell move) → still in-flight
    (1 * TIME_PER_CELL_MS,     '.',  'wK'), # exactly at arrival → landed
    (1 * TIME_PER_CELL_MS + 1, '.',  'wK'), # past arrival → landed
])
def test_apply_arrivals(clock_ms, origin, dest):
    # Arrange — 1-cell move: arrival_ms = 1 * TIME_PER_CELL_MS
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    state.clock_ms = clock_ms
    # Act
    state.apply_arrivals()
    # Assert
    assert state.board.get_token(0, 0) == origin
    assert state.board.get_token(0, 1) == dest



# ---------------------------------------------------------------------------
# is_in_flight
# ---------------------------------------------------------------------------

def test_is_in_flight_true_while_moving_false_after_arrival():
    # Arrange
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    # Assert — in-flight immediately after scheduling
    assert state.is_in_flight(BoardPosition(0, 0)) is True
    # Act — advance clock past arrival
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    # Assert — no longer in-flight once landed
    assert state.is_in_flight(BoardPosition(0, 0)) is False


# ---------------------------------------------------------------------------
# is_destination_reserved
# ---------------------------------------------------------------------------

def test_is_destination_reserved_blocks_second_piece():
    # Arrange — first piece already heading to (0, 2) (2-cell move)
    state = _state([['wK', 'wR', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 2, state.board))
    # Act / Assert — (0, 2) is reserved, (0, 1) is not
    assert state.is_destination_reserved(BoardPosition(0, 2)) is True
    assert state.is_destination_reserved(BoardPosition(0, 1)) is False


# ---------------------------------------------------------------------------
# game_over via king capture
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("attacker, victim, expected_status", [
    ('wR', 'bK', GameStatus.WHITE_WON),
    ('bR', 'wK', GameStatus.BLACK_WON),
])
def test_capturing_king_sets_game_status(attacker, victim, expected_status):
    # Arrange — attacker in-flight toward the enemy king
    state = _state([[attacker, victim]])
    state.schedule_move(MoveContext(attacker[1], attacker[0], 0, 0, 0, 1, state.board))
    # Act — advance clock to trigger arrival
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    # Assert
    assert state.status == expected_status


def test_schedule_move_ignored_after_game_over():
    # Arrange — force game over
    state = _state([['wR', 'bK', '.']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 1, state.board))
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == GameStatus.WHITE_WON
    # Act — attempt to schedule another move
    state.schedule_move(MoveContext('R', 'w', 0, 1, 0, 2, state.board))
    # Assert — in_flight remains empty; move was ignored
    assert state.in_flight == {}
