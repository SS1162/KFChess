import pytest

from board import Board
from commands import PrintBoardCommand, WaitCommand
from constants import JUMP_DURATION_MS, TIME_PER_CELL_MS
from exceptions import InvalidCommandArgumentError, UnknownCommandTargetError
from game_state import GameState
from game_status import GameStatus
from handlers.click import ClickCommandHandler, parse_click
from handlers.print_board import handle_print_board, parse_print
from handlers.wait import handle_wait, parse_wait
from models import BoardPosition
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


def test_handle_wait_calls_apply_landings():
    state = _state([['wK', '.']])
    state.schedule_jump(0, 0)
    handle_wait(WaitCommand(ms=JUMP_DURATION_MS), state)
    assert state.is_airborne(BoardPosition(0, 0)) is False


# ---------------------------------------------------------------------------
# handle_click — selection mechanics
# ---------------------------------------------------------------------------

def test_click_piece_selects_it():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.selection == BoardPosition(0, 0)


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
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.selection is None


def test_click_friendly_replaces_selection():
    state = _state([['wK', 'wR']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    assert state.selection == BoardPosition(0, 1)


# ---------------------------------------------------------------------------
# handle_click — move scheduling
# ---------------------------------------------------------------------------

def test_move_to_empty_cell_schedules_in_flight():
    state = _state([['wK', '.']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    assert state.board.get_token(0, 0) == 'wK'
    assert state.board.get_token(0, 1) == '.'
    assert state.selection is None
    assert state.is_in_flight(BoardPosition(0, 0))


# ---------------------------------------------------------------------------
# Flight interception guard
# ---------------------------------------------------------------------------

def test_redirecting_in_flight_piece_is_ignored():
    state = _state([['wK', '.', '.']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    original_entry = state.in_flight[BoardPosition(0, 0)]
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "250", "50"]), state)
    assert state.in_flight[BoardPosition(0, 0)] == original_entry


def test_move_captures_enemy_after_arrival():
    state = _state([['wK', 'bQ']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    handle_wait(WaitCommand(ms=1 * TIME_PER_CELL_MS), state)
    assert state.board.get_token(0, 1) == 'wK'
    assert state.board.get_token(0, 0) == '.'


# ---------------------------------------------------------------------------
# Real-time movement: in-flight visibility and arrival via wait
# ---------------------------------------------------------------------------

def test_move_is_in_flight_before_arrival(capsys):
    state = _state([['wK', '.']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    handle_print_board(PrintBoardCommand(), state)
    assert capsys.readouterr().out.split()[0] == 'wK'


def test_move_arrives_after_wait(capsys):
    state = _state([['wK', '.']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)
    handle_wait(WaitCommand(ms=1 * TIME_PER_CELL_MS), state)
    handle_print_board(PrintBoardCommand(), state)
    tokens = capsys.readouterr().out.split()
    assert tokens == ['.', 'wK']


# ---------------------------------------------------------------------------
# game-over guard: click move ignored after game over
# ---------------------------------------------------------------------------

def test_click_move_ignored_after_game_over():
    state = _state([['wR', 'bK', '.']])
    mv = MoveValidator()
    mv.register('R', lambda ctx: ctx.fr == ctx.tr)
    handler = ClickCommandHandler(mv)
    state.select(BoardPosition(0, 0))
    handler.execute(parse_click(["click", "150", "50"]), state)
    handle_wait(WaitCommand(ms=1 * TIME_PER_CELL_MS), state)
    assert state.status == GameStatus.WHITE_WON
    state.select(BoardPosition(0, 1))
    handler.execute(parse_click(["click", "250", "50"]), state)
    assert state.in_flight == {}


# ---------------------------------------------------------------------------
# Jump via double-click
# ---------------------------------------------------------------------------

def test_double_click_triggers_jump():
    # First click selects, second click on same cell triggers jump
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)   # select
    _handler().execute(parse_click(["click", "50", "50"]), state)   # jump
    assert state.is_airborne(BoardPosition(0, 0)) is True
    assert state.selection is None


def test_double_click_deselects_after_jump():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.selection is None


def test_double_click_on_in_flight_piece_does_not_jump():
    state = _state([['wK', '.']])
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)  # schedule move
    assert state.is_in_flight(BoardPosition(0, 0)) is True
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "50", "50"]), state)   # double-click while in-flight
    assert state.is_airborne(BoardPosition(0, 0)) is False


def test_double_click_on_already_airborne_piece_does_not_re_jump():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)   # select
    _handler().execute(parse_click(["click", "50", "50"]), state)   # jump
    original_land_at = state.airborne[BoardPosition(0, 0)]
    state.advance_clock(100)
    _handler().execute(parse_click(["click", "50", "50"]), state)   # select again
    _handler().execute(parse_click(["click", "50", "50"]), state)   # attempt re-jump
    assert state.airborne[BoardPosition(0, 0)] == original_land_at


def test_jump_piece_cannot_move_while_airborne():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)   # select
    _handler().execute(parse_click(["click", "50", "50"]), state)   # jump
    assert state.is_airborne(BoardPosition(0, 0)) is True
    state.select(BoardPosition(0, 0))
    _handler().execute(parse_click(["click", "150", "50"]), state)  # try to move
    assert state.in_flight == {}


def test_jump_expires_after_wait():
    state = _state([['wK', '.']])
    _handler().execute(parse_click(["click", "50", "50"]), state)
    _handler().execute(parse_click(["click", "50", "50"]), state)
    assert state.is_airborne(BoardPosition(0, 0)) is True
    handle_wait(WaitCommand(ms=JUMP_DURATION_MS), state)
    assert state.is_airborne(BoardPosition(0, 0)) is False


def test_jump_ignored_after_game_over():
    state = _state([['wR', 'bK', '.']])
    mv = MoveValidator()
    mv.register('R', lambda ctx: ctx.fr == ctx.tr)
    handler = ClickCommandHandler(mv)
    state.select(BoardPosition(0, 0))
    handler.execute(parse_click(["click", "150", "50"]), state)
    handle_wait(WaitCommand(ms=TIME_PER_CELL_MS), state)
    assert state.status == GameStatus.WHITE_WON
    # Attempt jump after game over
    handler.execute(parse_click(["click", "50", "50"]), state)   # select wR (now at 0,1)
    handler.execute(parse_click(["click", "50", "50"]), state)   # double-click
    assert state.airborne == {}
