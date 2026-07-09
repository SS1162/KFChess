import logging
from typing import List

from commands import ClickCommand
from constants import CELL_SIZE
from coordinate_translator import pixel_to_board
from exceptions import InvalidCommandArgumentError
from game_state import GameState
from models import BoardPosition, Point
from movement import MoveContext, MoveValidator

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
        pos = pixel_to_board(cmd.p.x, cmd.p.y, CELL_SIZE, state.board.rows, state.board.cols)
        if pos is None:
            logger.warning("Click (%d, %d) is out of bounds — ignored.", cmd.p.x, cmd.p.y)
            return
        if state.selection is None:
            self._handle_no_selection(pos, state)
        else:
            self._handle_selection(pos, state)

    def _handle_no_selection(self, pos: BoardPosition, state: GameState) -> None:
        token = state.board.get_token(pos.row, pos.col)
        if token == '.':
            return
        state.select(pos)
        logger.info("Selected %r at (%d, %d).", token, pos.row, pos.col)

    def _handle_selection(self, pos: BoardPosition, state: GameState) -> None:
        sel = state.selection
        if pos == sel:
            self._handle_double_click(pos, state)
            return
        sel_token = state.board.get_token(sel.row, sel.col)
        token = state.board.get_token(pos.row, pos.col)
        if token != '.' and token[0] == sel_token[0]:
            state.select(pos)
            return
        self._try_move(pos, sel, sel_token, state)

    def _handle_double_click(self, pos: BoardPosition, state: GameState) -> None:
        """Second click on the already-selected piece: attempt a jump, then deselect."""
        if (not state.is_in_flight(pos)
                and not state.is_airborne(pos)
                and state.board.get_token(pos.row, pos.col) != '.'):
            state.schedule_jump(pos.row, pos.col)
            logger.info("Jump triggered at (%d,%d).", pos.row, pos.col)
        state.deselect()

    def _try_move(self, pos: BoardPosition, sel: BoardPosition, sel_token: str, state: GameState) -> None:
        ctx = MoveContext(sel_token[1], sel_token[0], sel.row, sel.col, pos.row, pos.col, state.board)
        if not self._move_validator.is_legal(ctx):
            state.deselect()
            return
        if state.is_destination_reserved(pos):
            logger.warning("Destination (%d, %d) already reserved — move ignored.", pos.row, pos.col)
            state.deselect()
            return
        state.schedule_move(ctx)
        state.deselect()
