import logging
import sys

from board import Board
from exceptions import BoardError
from parser import TextBoardParser
from validator import BoardValidator

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


def _execute(command: str, board: Board) -> None:
    if command == 'print board':
        print(board)
    else:
        logger.warning("Unknown command ignored: %r", command)


def main() -> None:
    grid, commands = TextBoardParser().parse(sys.stdin)

    try:
        BoardValidator.validate(grid)
    except BoardError as exc:
        logger.error("Board rejected: %s", exc)
        print(f"ERROR {exc.error_code}")
        sys.exit(0)

    board = Board(rows=len(grid), cols=len(grid[0]), grid=grid)
    for command in commands:
        _execute(command, board)


if __name__ == '__main__':
    main()
