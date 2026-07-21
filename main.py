# Repository: https://github.com/SS1162/KFChess
import logging
import sys

from board import Board
from engine_factory import build_command_parser, build_executor, build_move_validator
from exceptions import BoardError
from game_state import GameState
from parser import TextBoardParser
from validator import BoardValidator

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s [%(name)s] %(message)s",
        filename="kfchess.log",
        filemode="w",
    )
    cmd_parser = build_command_parser()
    executor   = build_executor()

    grid, raw_commands = TextBoardParser().parse(sys.stdin)

    try:
        BoardValidator.validate(grid)
    except BoardError as exc:
        logger.error("Board rejected: %s", exc)
        print(f"ERROR {exc.error_code}")
        sys.exit(0)

    state = GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))

    for raw in raw_commands:
        cmd = cmd_parser.parse(raw)
        if cmd is not None:
            executor.execute(cmd, state)


if __name__ == '__main__':
    main()
