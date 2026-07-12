import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from exceptions import CommandError

logger = logging.getLogger(__name__)

_Factory = Callable[[List[str]], Any]


class CommandParser:
    """Registry-based parser: maps command keywords to factory callables.

    Register a keyword with a factory that receives the full split parts list
    and returns a Command object. Factories should raise a CommandError subclass
    (InvalidCommandArgumentError, UnknownCommandTargetError, …) or IndexError
    on bad input; both are caught here and logged as warnings.

    Example::
        cp = CommandParser()
        cp.register("click", lambda p: ClickCommand(int(p[1]), int(p[2])))
    """

    def __init__(self) -> None:
        self._parsers: Dict[str, _Factory] = {}

    def register(self, keyword: str, factory: _Factory) -> None:
        self._parsers[keyword] = factory

    def parse(self, line: str) -> Optional[Any]:
        parts = line.split()
        if not parts:
            return None
        factory = self._parsers.get(parts[0])
        if factory is None:
            logger.warning("Unknown command keyword %r — line ignored.", parts[0])
            return None
        try:
            return factory(parts)
        except (CommandError, IndexError) as exc:
            logger.warning("Malformed command %r: %s", line, exc)
            return None


class TextBoardParser:
    """Parses the Board: / Commands: input format into a grid and command list."""

    def _strip_blank_edges(self, lines: list) -> list:
        """Remove leading and trailing blank lines, logging counts."""
        leading = trailing = 0
        while lines and not lines[0].strip():
            lines.pop(0)
            leading += 1
        while lines and not lines[-1].strip():
            lines.pop()
            trailing += 1
        if leading:
            logger.warning("Stripped %d leading blank line(s) from board section.", leading)
        if trailing:
            logger.warning("Stripped %d trailing blank line(s) from board section.", trailing)
        return lines

    def parse(self, source) -> Tuple[List[List[str]], List[str]]:
        lines = [line.rstrip('\n') for line in source]
        stripped = [line.strip() for line in lines]

        try:
            board_start = stripped.index('Board:') + 1
        except ValueError:
            logger.warning("No 'Board:' header found; treating entire input as board.")
            board_start = 0

        try:
            commands_idx = stripped.index('Commands:')
        except ValueError:
            logger.warning("No 'Commands:' header found; no commands will be executed.")
            commands_idx = len(lines)

        board_lines = self._strip_blank_edges(lines[board_start:commands_idx])
        command_lines = lines[commands_idx + 1:]

        grid = [line.split() for line in board_lines if line.strip()]
        commands = [line.strip() for line in command_lines if line.strip()]

        return grid, commands
