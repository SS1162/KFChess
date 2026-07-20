import logging
from typing import List

from commands import JumpCommand
from constants import CELL_SIZE
from coordinate_translator import pixel_to_board
from exceptions import InvalidCommandArgumentError
from game_state import GameState
from models import Point

logger = logging.getLogger(__name__)


def parse_jump(parts: List[str]) -> JumpCommand:
    try:
        return JumpCommand(p=Point(x=int(parts[1]), y=int(parts[2])))
    except (IndexError, ValueError):
        raise InvalidCommandArgumentError(
            command='jump',
            argument='x y',
            value=parts[1:3],
            reason='x and y must be integers',
        )


def handle_jump(cmd: JumpCommand, state: GameState) -> None:
    cs = cmd.cell_size if cmd.cell_size > 0 else CELL_SIZE
    pos = pixel_to_board(cmd.p.x, cmd.p.y, cs, state.board.rows, state.board.cols)
    if pos is None:
        logger.warning("Jump (%d, %d) is out of bounds — ignored.", cmd.p.x, cmd.p.y)
        return
    token = state.board.get_token(pos.row, pos.col)
    if token == '.':
        logger.warning("Jump ignored — no piece at (%d,%d).", pos.row, pos.col)
        return
    state.schedule_jump(pos.row, pos.col)
