import asyncio
import functools
import logging
import sys

import websockets

from board import Board
from connection_manager import ConnectionManager
from exceptions import BoardError
from game_session import GameSession
from game_state import GameState
from parser import TextBoardParser
from validator import BoardValidator

# server.py is its own entry point (run directly via `python server.py`), so it
# owns its logging configuration independently of main.py. basicConfig only
# takes effect on its first call in a process — if server.py ever imports
# main.py (or anything that calls basicConfig) in the future, only one of the
# two configurations will apply, so this must stay the ONLY basicConfig call
# reachable when running server.py.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
    filename="kfchess.log",
    filemode="w",
)

logger = logging.getLogger(__name__)

DEFAULT_BOARD_FILE = "starting_position.txt"


def _load_game_session() -> GameSession:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOARD_FILE
    try:
        with open(path) as f:
            grid, _ = TextBoardParser().parse(f)
    except OSError as exc:
        logger.error("Cannot open board file %r: %s", path, exc)
        sys.exit(1)

    try:
        BoardValidator.validate(grid)
    except BoardError as exc:
        logger.error("Board validation failed for %r: %s", path, exc)
        sys.exit(1)

    state = GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))
    return GameSession(state)


async def handler(websocket, connection_manager, game_session) -> None:
    await connection_manager.register(websocket)
    try:
        async for raw in websocket:
            result = game_session.apply_command(raw)
            await connection_manager.broadcast(result)
    finally:
        await connection_manager.unregister(websocket)


async def main() -> None:
    connection_manager = ConnectionManager()
    game_session = _load_game_session()
    _handler = functools.partial(handler, connection_manager=connection_manager, game_session=game_session)
    async with websockets.serve(_handler, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
