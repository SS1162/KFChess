import pytest

from board import Board
from commands import PrintBoardCommand, WaitCommand
from constants import TIME_PER_CELL_MS
from exceptions import InvalidCommandArgumentError, UnknownCommandTargetError
from game_state import GameState
from handlers.click import ClickCommandHandler, parse_click
from handlers.print_board import handle_print_board, parse_print
from handlers.wait import handle_wait, parse_wait
from movement import MoveValidator, king_can_move, pawn_can_move


def _state(token_rows):
    board = Board(rows=len(token_rows), cols=len(token_rows[0]), grid=[list(r) for r in token_rows])
    return GameState(board=board)


def _handler():
    """ClickCommandHandler wired with King and Pawn validators."""
    mv = MoveValidator()
    mv.register('K', king_can_move)
    mv.register('P', pawn_can_move)
    return ClickCommandHandler(mv)


# ---------------------------------------------------------------------------
# parse_wait
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ms", [0, 1, 9999])
def test_parse_wait_valid(ms):
    assert parse_wait(["wait", str(ms)]) == WaitCommand(ms=ms)


@pytest.mark.parametrize("args", [["wait", "-1"], ["wait", "abc"], ["wait"]])
def test_parse_wait_invalid_raises(args):
    with pytest.raises(InvalidCommandArgumentError):
        parse_wait(args)


# ---------------------------------------------------------------------------
# parse_print
# ---------------------------------------------------------------------------

def test_parse_print_board_returns_command():
    assert parse_print(["print", "board"]) == PrintBoardCommand()


@pytest.mark.parametrize("args", [["print", "clock"], ["print"]])
def test_parse_print_unknown_target_raises(args):
    with pytest.raises(UnknownCommandTargetError):
        parse_print(args)


# ---------------------------------------------------------------------------
# parse_click
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("args", [["click", "abc", "50"], ["click", "50"], ["click"]])
def test_parse_click_invalid_raises(args):
    with pytest.raises(InvalidCommandArgumentError):
        parse_click(args)


# ---------------------------------------------------------------------------
# handle_wait
# ---------------------------------------------------------------------------

def test_handle_wait_advances_clock():
    state = _state([['.']])
    handle_wait(WaitCommand(ms=500), state)
    assert state.clock_ms == 500


# ---------------------------------------------------------------------------
# handle_click — selection mechanics
# ---------------------------------------------------------------------------

def test_click_piece_selects_it():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.selection == (0, 0)


def test_click_empty_cell_does_not_select():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "150", "50"]), state)
    assert state.selection is None


@pytest.mark.parametrize("x,y", [(-10, 50), (300, 50), (50, 300)])
def test_click_out_of_bounds_is_ignored(x, y):
    state = _state([['wK', '.'], ['.', '.']])
    _handler().execute(parse_click(["click", str(x), str(y)]), state)
    assert state.selection is None


def test_click_selected_piece_again_deselects():
    state = _state([['wK', '.']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.selection is None


def test_click_friendly_replaces_selection():
    state = _state([['wK', 'wR']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "150", "50"]), state)
    assert state.selection == (0, 1)





# ---------------------------------------------------------------------------
# handle_click — move scheduling (moves are now deferred, not instant)
# ---------------------------------------------------------------------------

def test_move_to_empty_cell_schedules_in_flight():
    # Arrange
    state = _state([['wK', '.']])
    state.select(0, 0)
    # Act
    _handler().execute(parse_click(["click", "150", "50"]), state)
    # Assert — piece in-flight: board unchanged, selection cleared
    assert state.board.get_token(0, 0) == 'wK'
    assert state.board.get_token(0, 1) == '.'
    assert state.selection is None
    assert state.is_in_flight(0, 0)


# ---------------------------------------------------------------------------
# Flight interception guard
# ---------------------------------------------------------------------------

def test_redirecting_in_flight_piece_is_ignored():
    # Arrange — schedule a move for the King
    state = _state([['wK', '.', '.']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "150", "50"]), state)  # King \u2192 (0,1), in-flight
    original_entry = state.in_flight[(0, 0)]
    # Act — try to redirect the same King while it's still in-flight
    # (GameState.schedule_move silently ignores the request; handler still deselects)
    state.select(0, 0)
    _handler().execute(parse_click(["click", "250", "50"]), state)  # attempt King \u2192 (0,2)
    # Assert — original in-flight entry is unchanged
    assert state.in_flight[(0, 0)] == original_entry


def test_move_captures_enemy_after_arrival():
    # Arrange
    state = _state([['wK', 'bQ']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "150", "50"]), state)
    # Act — advance clock to trigger arrival (1-cell move)
    handle_wait(WaitCommand(ms=1 * TIME_PER_CELL_MS), state)
    # Assert — piece landed, enemy captured
    assert state.board.get_token(0, 1) == 'wK'
    assert state.board.get_token(0, 0) == '.'


# ---------------------------------------------------------------------------
# Real-time movement: in-flight visibility and arrival via wait
# ---------------------------------------------------------------------------

def test_move_is_in_flight_before_arrival(capsys):
    # Arrange — schedule a move
    state = _state([['wK', '.']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "150", "50"]), state)
    # Act — print board before any wait
    handle_print_board(PrintBoardCommand(), state)
    # Assert — piece still at origin
    assert capsys.readouterr().out.split()[0] == 'wK'


def test_move_arrives_after_wait(capsys):
    # Arrange — schedule a move
    state = _state([['wK', '.']])
    state.select(0, 0)
    _handler().execute(parse_click(["click", "150", "50"]), state)
    # Act — advance clock past arrival (1-cell move), then print
    handle_wait(WaitCommand(ms=1 * TIME_PER_CELL_MS), state)
    handle_print_board(PrintBoardCommand(), state)
    # Assert — piece at destination
    tokens = capsys.readouterr().out.split()
    assert tokens == ['.', 'wK']
