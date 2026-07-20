from game_state import GameState
from main import _build_command_parser, _build_executor

_cmd_parser = _build_command_parser()
_executor = _build_executor()


def run_single_command(state: GameState, raw_command: str) -> GameState:
    cmd = _cmd_parser.parse(raw_command)
    if cmd is not None:
        _executor.execute(cmd, state)
    return state
