from engine_factory import build_command_parser, build_executor
from game_state import GameState

_cmd_parser = build_command_parser()
_executor = build_executor()


def run_single_command(state: GameState, raw_command: str) -> GameState:
    cmd = _cmd_parser.parse(raw_command)
    if cmd is not None:
        _executor.execute(cmd, state)
    return state
