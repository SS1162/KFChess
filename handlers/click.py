import logging
from typing import List

from commands import ClickCommand
from constants import CELL_SIZE
from exceptions import InvalidCommandArgumentError
from game_state import GameState
from movement import MoveContext, MoveValidator

from models import Point

logger = logging.getLogger(__name__)


def parse_click(parts: List[str]) -> ClickCommand:
    try:
        return ClickCommand(p=Point(x=int(parts[1]), y=int(parts[2])))
    except (IndexError, ValueError):
        raise InvalidCommandArgumentError(
            command='click',
            argument='x y',
            value=parts[1:3],
            reason='x and y must be integers',
        )


class ClickCommandHandler:
    """Handles ClickCommand events. Receives a MoveValidator at construction time."""

    def __init__(self, move_validator: MoveValidator) -> None:
        self._move_validator = move_validator

    def execute(self, cmd: ClickCommand, state: GameState) -> None:
        col = cmd.p.x // CELL_SIZE
        row = cmd.p.y // CELL_SIZE

        if not (0 <= row < state.board.rows and 0 <= col < state.board.cols):
            logger.warning("Click (%d, %d) is out of bounds — ignored.", cmd.p.x, cmd.p.y)
            return

        token = state.board.get_token(row, col)

        if state.selection is None:
            # No active selection: try to select the clicked piece.
            if token == '.':
                return
            state.select(row, col)
            logger.info("Selected %r at (%d, %d).", token, row, col)

        else:
            sel_row, sel_col = state.selection
            sel_token = state.board.get_token(sel_row, sel_col)

            if (row, col) == (sel_row, sel_col):
                state.deselect()  # clicking selected piece again → deselect
                return

            is_friendly = (token != '.' and token[0] == sel_token[0])

            if is_friendly:
                state.select(row, col)  # replace selection with available friendly
                return

            # Empty cell or enemy: validate move shape before applying.
            color      = sel_token[0]
            piece_type = sel_token[1]
            ctx = MoveContext(piece_type, color, sel_row, sel_col, row, col, state.board)
            if not self._move_validator.is_legal(ctx):
                state.deselect()
                return

            if state.is_destination_reserved(row, col):
                logger.warning("Destination (%d, %d) already reserved by an in-flight piece — move ignored.", row, col)
                state.deselect()
                return

            state.schedule_move(ctx)
            state.deselect()
