from board import Board
from command_executor import CommandExecutor
from commands import WaitCommand
from game_state import GameState
from handlers.wait import handle_wait, parse_wait
from parser import CommandParser


def _build():
    cp = CommandParser()
    cp.register("wait", parse_wait)
    ex = CommandExecutor()
    ex.register(WaitCommand, handle_wait)
    board = Board(rows=1, cols=1, grid=[['.']])
    state = GameState(board=board)
    return cp, ex, state


def test_command_executor_end_to_end_via_raw_string():
    cp, ex, state = _build()
    cmd = cp.parse("wait 500")
    assert cmd is not None
    ex.execute(cmd, state)
    assert state.clock_ms == 500
