import logging
from typing import List

from commands import WaitCommand
from exceptions import InvalidCommandArgumentError
from game_state import GameState

logger = logging.getLogger(__name__)


def parse_wait(parts: List[str]) -> WaitCommand:
    try:
        ms = int(parts[1])
    except (IndexError, ValueError):
        raise InvalidCommandArgumentError(
            command='wait',
            argument='ms',
            value=parts[1] if len(parts) > 1 else '<missing>',
            reason='must be a non-negative integer',
        )
    if ms < 0:
        raise InvalidCommandArgumentError(
            command='wait',
            argument='ms',
            value=ms,
            reason='duration must be a non-negative integer',
        )
    return WaitCommand(ms=ms)


def handle_wait(cmd: WaitCommand, state: GameState) -> None:
    state.advance_clock(cmd.ms)
    state.apply_arrivals()
    state.apply_landings()
    logger.info("Clock advanced by %d ms → now at %d ms.", cmd.ms, state.clock_ms)
