# GameSession receives a pre-built GameState via its constructor and does not
# construct one itself. Callers are responsible for building the initial state
# (e.g. by parsing a board with TextBoardParser and passing it to GameState).
import logging
from dataclasses import asdict

import engine_adapter
import protocol
from game_state import GameState
from protocol import ErrorMessage

logger = logging.getLogger(__name__)


class GameSession:
    def __init__(self, state: GameState) -> None:
        self.state = state

    def apply_command(self, raw: str) -> dict:
        try:
            parsed = protocol.parse_incoming(raw)
        except protocol.ProtocolError as exc:
            logger.warning("Invalid incoming message: %s", exc)
            return asdict(ErrorMessage(reason=str(exc)))

        try:
            engine_adapter.run_single_command(self.state, parsed.raw)
        except Exception as exc:
            logger.warning("Engine error processing command %r: %s", raw, exc)
            return asdict(ErrorMessage(reason=str(exc)))

        return protocol.serialize_state(self.state)
