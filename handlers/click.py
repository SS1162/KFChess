import logging
from typing import List

from commands import ClickCommand
from config import CELL_SIZE
from game_state import GameState

logger = logging.getLogger(__name__)


def parse_click(parts: List[str]) -> ClickCommand:
    return ClickCommand(x=int(parts[1]), y=int(parts[2]))


def handle_click(cmd: ClickCommand, state: GameState) -> None:
    col = cmd.x // CELL_SIZE
    row = cmd.y // CELL_SIZE

    if not (0 <= row < state.board.rows and 0 <= col < state.board.cols):
        logger.warning("Click (%d, %d) is out of bounds — ignored.", cmd.x, cmd.y)
        return

    token = state.board.grid[row][col]

    if state.selection is None:
        # No active selection: try to select the clicked piece.
        if token == '.' or state.is_in_cooldown(row, col):
            return
        state.selection = (row, col)
        logger.info("Selected %r at (%d, %d).", token, row, col)

    else:
        sel_row, sel_col = state.selection
        sel_token = state.board.grid[sel_row][sel_col]

        if (row, col) == (sel_row, sel_col):
            state.selection = None  # clicking selected piece again → deselect
            return

        is_friendly = (token != '.' and token[0] == sel_token[0])

        if is_friendly:
            if state.is_in_cooldown(row, col):
                logger.warning("Friendly piece at (%d, %d) is in cooldown — click ignored.", row, col)
                return
            state.selection = (row, col)  # replace selection with available friendly
            return

        # Empty cell or enemy → instant move (captures enemy if present).
        state.apply_move(sel_row, sel_col, row, col)
        state.selection = None
