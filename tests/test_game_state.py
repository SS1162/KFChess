import pytest

from board import Board
from constants import JUMP_DURATION_MS, TIME_PER_CELL_MS
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
    state = _state([['wK', '.']])
    state.select(BoardPosition(0, 0))
    assert state.selection == BoardPosition(0, 0)
    state.deselect()
    assert state.selection is None


def test_apply_move_updates_board():
    state = _state([['wK', '.']])
    state.apply_move(Move(0, 0, 0, 1))
    assert state.board.get_token(0, 0) == '.'
    assert state.board.get_token(0, 1) == 'wK'


# ---------------------------------------------------------------------------
# schedule_move
# ---------------------------------------------------------------------------

def test_schedule_move_piece_stays_at_origin():
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    assert state.board.get_token(0, 0) == 'wK'
    assert state.board.get_token(0, 1) == '.'


def test_schedule_move_ignores_already_in_flight():
    state = _state([['wK', '.', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    original_entry = state.in_flight[BoardPosition(0, 0)]
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 2, state.board))
    assert state.in_flight[BoardPosition(0, 0)] == original_entry


# ---------------------------------------------------------------------------
# apply_arrivals
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("clock_ms, origin, dest", [
    (1 * TIME_PER_CELL_MS - 1, 'wK', '.'),
    (1 * TIME_PER_CELL_MS,     '.',  'wK'),
    (1 * TIME_PER_CELL_MS + 1, '.',  'wK'),
])
def test_apply_arrivals(clock_ms, origin, dest):
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    state.clock_ms = clock_ms
    state.apply_arrivals()
    assert state.board.get_token(0, 0) == origin
    assert state.board.get_token(0, 1) == dest


# ---------------------------------------------------------------------------
# is_in_flight
# ---------------------------------------------------------------------------

def test_is_in_flight_true_while_moving_false_after_arrival():
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    assert state.is_in_flight(BoardPosition(0, 0)) is True
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.is_in_flight(BoardPosition(0, 0)) is False


# ---------------------------------------------------------------------------
# is_destination_reserved
# ---------------------------------------------------------------------------

def test_is_destination_reserved_blocks_second_piece():
    state = _state([['wK', 'wR', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 2, state.board))
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
    state = _state([[attacker, victim]])
    state.schedule_move(MoveContext(attacker[1], attacker[0], 0, 0, 0, 1, state.board))
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == expected_status


def test_schedule_move_ignored_after_game_over():
    state = _state([['wR', 'bK', '.']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 1, state.board))
    state.clock_ms = 1 * TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == GameStatus.WHITE_WON
    state.schedule_move(MoveContext('R', 'w', 0, 1, 0, 2, state.board))
    assert state.in_flight == {}


# ---------------------------------------------------------------------------
# schedule_jump
# ---------------------------------------------------------------------------

def test_schedule_jump_registers_airborne():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    assert state.is_airborne(BoardPosition(0, 0)) is True
    assert state.airborne[BoardPosition(0, 0)] == JUMP_DURATION_MS
    assert state.board.get_token(0, 0) == 'wK'


def test_schedule_jump_ignored_if_in_flight():
    state = _state([['wK', '.']])
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    state.schedule_jump(0, 0)
    assert state.is_airborne(BoardPosition(0, 0)) is False


def test_schedule_jump_ignored_if_already_airborne():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    original_land_at = state.airborne[BoardPosition(0, 0)]
    state.advance_clock(100)
    state.schedule_jump(0, 0)
    assert state.airborne[BoardPosition(0, 0)] == original_land_at


def test_schedule_jump_ignored_on_empty_cell():
    state = _state([['.']])
    state.schedule_jump(0, 0)
    assert state.airborne == {}


def test_schedule_jump_ignored_after_game_over():
    state = _state([['wR', 'bK']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 1, state.board))
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == GameStatus.WHITE_WON
    state.schedule_jump(0, 1)
    assert state.airborne == {}


# ---------------------------------------------------------------------------
# apply_landings
# ---------------------------------------------------------------------------

def test_apply_landings_clears_expired_airborne():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    state.clock_ms = JUMP_DURATION_MS
    state.apply_landings()
    assert state.is_airborne(BoardPosition(0, 0)) is False
    assert state.airborne == {}


def test_apply_landings_does_not_clear_active_airborne():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    state.clock_ms = JUMP_DURATION_MS - 1
    state.apply_landings()
    assert state.is_airborne(BoardPosition(0, 0)) is True


def test_apply_landings_multiple_pieces_partial_expiry():
    # wK jumps at clock=0 → lands at 1000; wR jumps at clock=200 → lands at 1200
    state = _state([['wK', 'wR', '.']])
    state.schedule_jump(0, 0)
    state.advance_clock(200)
    state.schedule_jump(0, 1)
    state.clock_ms = JUMP_DURATION_MS  # = 1000: wK expired, wR still airborne
    state.apply_landings()
    assert state.is_airborne(BoardPosition(0, 0)) is False
    assert state.is_airborne(BoardPosition(0, 1)) is True


# ---------------------------------------------------------------------------
# schedule_move lockdown: airborne piece cannot move
# ---------------------------------------------------------------------------

def test_schedule_move_ignored_if_airborne():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    state.schedule_move(MoveContext('K', 'w', 0, 0, 0, 1, state.board))
    assert state.in_flight == {}


# ---------------------------------------------------------------------------
# Air capture
# ---------------------------------------------------------------------------

def test_air_capture_removes_arriving_enemy_keeps_airborne_piece():
    # wK airborne at (0,0); bR arrives at (0,0) during jump window
    state = _state([['wK', 'bR']])
    state.schedule_jump(0, 0)
    state.schedule_move(MoveContext('R', 'b', 0, 1, 0, 0, state.board))
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.board.get_token(0, 0) == 'wK'
    assert state.board.get_token(0, 1) == '.'  # bR removed from its origin
    assert state.in_flight == {}
    assert state.is_airborne(BoardPosition(0, 0)) is False


def test_air_capture_arriving_king_triggers_game_over():
    # wR airborne at (0,1); bK arrives at (0,1) → bK captured → WHITE_WON
    state = _state([['bK', 'wR']])
    state.schedule_jump(0, 1)
    state.schedule_move(MoveContext('K', 'b', 0, 0, 0, 1, state.board))
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == GameStatus.WHITE_WON
    assert state.board.get_token(0, 1) == 'wR'
    assert state.is_airborne(BoardPosition(0, 1)) is False


def test_air_capture_non_king_does_not_trigger_game_over():
    # wK airborne at (0,0); bR arrives → bR captured → no game over
    state = _state([['wK', 'bR']])
    state.schedule_jump(0, 0)
    state.schedule_move(MoveContext('R', 'b', 0, 1, 0, 0, state.board))
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.status == GameStatus.PLAYING


def test_no_air_capture_for_same_color():
    # wK airborne at (0,0); wR arrives at (0,0) — same color, normal landing
    state = _state([['wK', 'wR', '.']])
    state.schedule_jump(0, 0)
    state.schedule_move(MoveContext('R', 'w', 0, 1, 0, 0, state.board))
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    # wR lands normally on (0,0), capturing wK (friendly fire via normal landing)
    assert state.board.get_token(0, 0) == 'wR'
    assert state.board.get_token(0, 1) == '.'


def test_air_capture_same_ms_as_jump_start():
    # Enemy arrives at exact same ms the jump was scheduled (clock=0, arrival_ms=0)
    # Jump scheduled at clock=0 → land_at=1000; move distance=0 is invalid so use 1-cell
    # arriving at ms=1000 while jump window is [0, 1000) — jump ends at 1000 so no capture
    # Use arrival_ms < JUMP_DURATION_MS to confirm capture happens inside window
    state = _state([['wK', 'bR']])
    state.schedule_jump(0, 0)                                              # land_at = 1000
    state.schedule_move(MoveContext('R', 'b', 0, 1, 0, 0, state.board))   # arrival_ms = 1000
    # At clock=999 arrival not yet due; at clock=1000 both expire simultaneously
    # Per blueprint: jump processed FIRST → piece is airborne at arrival_ms=1000 → air capture
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()   # arrival processed while airborne entry still present
    assert state.board.get_token(0, 0) == 'wK'
    assert state.is_airborne(BoardPosition(0, 0)) is False  # ended by capture


def test_air_capture_skipped_when_origin_token_missing():
    # Edge: origin cell is empty by the time apply_arrivals runs → _try_air_capture returns False
    # and _land_piece handles the empty move (no crash, no air capture).
    state = _state([['wK', 'bR']])
    state.schedule_jump(0, 0)                                              # wK airborne at (0,0)
    state.schedule_move(MoveContext('R', 'b', 0, 1, 0, 0, state.board))   # bR → (0,0)
    # Manually clear the origin so arriving_token == '.'
    state.board.set_token(0, 1, '.')
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()   # _try_air_capture sees '.' at origin → returns False
    # No air capture; _land_piece runs; wK still on board (not captured)
    assert state.board.get_token(0, 0) == 'wK'


def test_cancel_blocked_removes_in_flight_piece_when_path_obstructed():
    # wR at (0,0) heading to (0,2); wN placed at (0,1) blocks the path mid-flight.
    state = _state([['wR', '.', '.']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 2, state.board))
    assert state.is_in_flight(BoardPosition(0, 0))
    # Obstruct the path before arrival
    state.board.set_token(0, 1, 'wN')
    state._cancel_blocked()
    assert not state.is_in_flight(BoardPosition(0, 0))


def test_cancel_captured_at_destination_removes_pieces_heading_there():
    # wR at (0,0) and wQ at (0,2) both heading to (0,1).
    # A third piece lands on (0,1) first; both in-flight pieces must be cancelled.
    state = _state([['wR', '.', 'wQ']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 1, state.board))
    state.schedule_move(MoveContext('Q', 'w', 0, 2, 0, 1, state.board))
    dest = BoardPosition(0, 1)
    state._cancel_captured_at_destination(dest)
    assert BoardPosition(0, 0) not in state.in_flight
    assert BoardPosition(0, 2) not in state.in_flight


def test_cancel_blocked_triggered_via_apply_arrivals():
    # wR at (0,0) heading to (0,2); wN arrives at (0,1) at the same tick,
    # blocking wR's path — _land_piece calls _cancel_blocked (step D).
    state = _state([['wR', 'wN', '.', '.']])
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 3, state.board))  # arrival_ms = 3000
    state.schedule_move(MoveContext('N', 'w', 0, 1, 0, 2, state.board))  # arrival_ms = 1000
    state.clock_ms = TIME_PER_CELL_MS  # only wN due
    state.apply_arrivals()             # wN lands at (0,2), blocking wR's path
    state.clock_ms = 3 * TIME_PER_CELL_MS
    state.apply_arrivals()             # _cancel_blocked fires; wR never arrives
    assert state.board.get_token(0, 0) == 'wR'
    assert not state.is_in_flight(BoardPosition(0, 0))


def test_cancel_captured_at_destination_triggered_via_apply_arrivals():
    # bQ at (0,2) and wR at (0,0) both head to (0,1).
    # bQ arrives first (1 cell, ms=1000); _land_piece calls _cancel_captured_at_destination
    # which removes wR's in-flight entry before wR's arrival_ms is due.
    state = _state([['wR', '.', 'bQ']])
    state.schedule_move(MoveContext('Q', 'b', 0, 2, 0, 1, state.board))  # arrival_ms = 1000
    state.schedule_move(MoveContext('R', 'w', 0, 0, 0, 1, state.board))  # arrival_ms = 1000
    # Advance only enough for bQ (sorted earliest-first; both equal — bQ cancels wR via step C)
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.board.get_token(0, 1) == 'bQ'
    assert not state.is_in_flight(BoardPosition(0, 0))


def test_multiple_enemies_arrive_only_first_triggers_air_capture():
    # wK airborne at (0,0); two enemies scheduled to arrive at (0,0)
    # First arrival triggers air capture (jump ends); second arrival lands normally
    state = _state([['wK', 'bR', 'bQ']])
    state.schedule_jump(0, 0)
    # bR arrives at ms=1000 (1 cell), bQ arrives at ms=2000 (2 cells)
    state.schedule_move(MoveContext('R', 'b', 0, 1, 0, 0, state.board))
    state.schedule_move(MoveContext('Q', 'b', 0, 2, 0, 0, state.board))
    # First tick: bR arrives, air capture fires, jump ends
    state.clock_ms = TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.board.get_token(0, 0) == 'wK'
    assert state.is_airborne(BoardPosition(0, 0)) is False
    # Second tick: bQ arrives, no longer airborne → normal landing captures wK
    state.clock_ms = 2 * TIME_PER_CELL_MS
    state.apply_arrivals()
    assert state.board.get_token(0, 0) == 'bQ'
