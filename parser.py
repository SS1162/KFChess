import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class TextBoardParser:
    """Parses the Board: / Commands: input format into a grid and command list."""

    def parse(self, source) -> Tuple[List[List[str]], List[str]]:
        lines = [line.rstrip('\n') for line in source]

        try:
            board_start = lines.index('Board:') + 1
        except ValueError:
            logger.warning("No 'Board:' header found; treating entire input as board.")
            board_start = 0

        try:
            commands_idx = lines.index('Commands:')
        except ValueError:
            logger.warning("No 'Commands:' header found; no commands will be executed.")
            commands_idx = len(lines)

        board_lines = lines[board_start:commands_idx]
        command_lines = lines[commands_idx + 1:]

        # Strip leading/trailing blank lines from the board section.
        leading = trailing = 0
        while board_lines and not board_lines[0].strip():
            board_lines.pop(0)
            leading += 1
        while board_lines and not board_lines[-1].strip():
            board_lines.pop()
            trailing += 1
        if leading:
            logger.warning("Stripped %d leading blank line(s) from board section.", leading)
        if trailing:
            logger.warning("Stripped %d trailing blank line(s) from board section.", trailing)

        grid = [line.split() for line in board_lines if line.strip()]
        commands = [line.strip() for line in command_lines if line.strip()]

        return grid, commands
