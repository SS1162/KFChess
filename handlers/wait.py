import logging
from typing import List

from commands import WaitCommand
from exceptions import InvalidCommandArgumentError
from game_state import GameState

logger = logging.getLogger(__name__)


def parse_wait(parts: List[str]) -> WaitCommand:
    ms = int(parts[1])
    if ms < 0:
        raise InvalidCommandArgumentError(
            command='wait',
            argument='ms',
            value=ms,
            reason='duration must be a non-negative integer',
        )
    return WaitCommand(ms=ms)


def handle_wait(cmd: WaitCommand, state: GameState) -> None:
    state.clock_ms += cmd.ms
    logger.info("Clock advanced by %d ms → now at %d ms.", cmd.ms, state.clock_ms)
