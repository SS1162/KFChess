import logging
from typing import List

from commands import PrintBoardCommand
from exceptions import UnknownCommandTargetError
from game_state import GameState

logger = logging.getLogger(__name__)


def parse_print(parts: List[str]) -> PrintBoardCommand:
    # Dispatches on first word "print"; second word selects the target.
    # Future targets (e.g. "print clock") can be handled here without
    # changing any infrastructure.
    if len(parts) < 2 or parts[1] != 'board':
        target = parts[1] if len(parts) >= 2 else '<none>'
        raise UnknownCommandTargetError(command='print', target=target)
    return PrintBoardCommand()


def handle_print_board(cmd: PrintBoardCommand, state: GameState) -> None:
    print(state.board)
