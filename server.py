import asyncio
import functools
import json
import logging
import sys

import websockets

from account_service import AccountError, AccountService
from bus_factory import build_bus
from board import Board
from connection_manager import ConnectionManager
from dataclasses import asdict
from exceptions import BoardError
from game_session import GameSession
from game_state import GameState
from parser import TextBoardParser
from player_registry import GameFullError, PlayerRegistry
from protocol import ErrorMessage, JoinAck, parse_join
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


def _load_game_session() -> GameState:
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
    return state


async def handler(websocket, connection_manager, game_session, player_registry, account_service) -> None:
    await connection_manager.register(websocket)
    try:
        async for raw in websocket:

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                await connection_manager.send_to(
                    websocket,
                    asdict(ErrorMessage(reason=f"Malformed JSON: {raw!r}")),
                )
                continue
            msg_type = parsed.get("type") if isinstance(parsed, dict) else None

            if msg_type == "join":
                join_request = parse_join(parsed)
                try:
                    elo = account_service.login_or_register(join_request.username, join_request.password)
                except AccountError as exc:
                    await connection_manager.send_to(
                        websocket,
                        asdict(ErrorMessage(reason=str(exc))),
                    )
                    continue
                try:
                    color = player_registry.register(websocket, join_request.username)
                except GameFullError as exc:
                    await connection_manager.send_to(
                        websocket,
                        asdict(ErrorMessage(reason=str(exc))),
                    )
                    await websocket.close()
                    continue
                await connection_manager.send_to(
                    websocket,
                    asdict(JoinAck(username=join_request.username, color=color, elo=elo)),
                )
            elif msg_type == "command":
                result = game_session.apply_command(parsed)
                await connection_manager.broadcast(result)
            else:
                await connection_manager.send_to(
                    websocket,
                    asdict(ErrorMessage(reason=f"Unknown message type: {msg_type!r}")),
                )
    finally:
        await connection_manager.unregister(websocket)
        player_registry.unregister(websocket)


async def main() -> None:
    connection_manager = ConnectionManager()
    bus = build_bus()
    game_session = GameSession(_load_game_session(), bus)
    account_service = AccountService("accounts.db")
    player_registry = PlayerRegistry()
    _handler = functools.partial(handler, connection_manager=connection_manager, game_session=game_session, player_registry=player_registry, account_service=account_service)
    async with websockets.serve(_handler, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
