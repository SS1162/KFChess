import logging
import sys

from board import Board
from command_executor import CommandExecutor
from commands import ClickCommand, PrintBoardCommand, WaitCommand
from exceptions import BoardError
from game_state import GameState
from handlers.click import handle_click, parse_click
from handlers.print_board import handle_print_board, parse_print
from handlers.wait import handle_wait, parse_wait
from parser import CommandParser, TextBoardParser
from validator import BoardValidator

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)


def _build_command_parser() -> CommandParser:
    cp = CommandParser()
    cp.register("click", parse_click)
    cp.register("wait",  parse_wait)
    cp.register("print", parse_print)
    return cp


def _build_executor() -> CommandExecutor:
    ex = CommandExecutor()
    ex.register(ClickCommand,      handle_click)
    ex.register(WaitCommand,       handle_wait)
    ex.register(PrintBoardCommand, handle_print_board)
    return ex


def main() -> None:
    cmd_parser = _build_command_parser()
    executor   = _build_executor()

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
