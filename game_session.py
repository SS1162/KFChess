# GameSession receives a pre-built GameState and a Bus via its constructor and
# does not construct either itself. Callers are responsible for building the
# initial state and bus and passing them in. GameSession depends on protocol.py,
# engine_adapter.py, and bus.py.
import logging
from dataclasses import asdict

import engine_adapter
import protocol
from bus import Bus
from game_state import GameState
from protocol import ErrorMessage

logger = logging.getLogger(__name__)


class GameSession:
    def __init__(self, state: GameState, bus: Bus) -> None:
        self.state = state
        self.bus = bus

    def apply_command(self, parsed: dict) -> dict:
        try:
            parsed_cmd = protocol.parse_incoming(parsed)
        except protocol.ProtocolError as exc:
            logger.warning("Invalid incoming message: %s", exc)
            return asdict(ErrorMessage(reason=str(exc)))

        try:
            engine_adapter.run_single_command(self.state, parsed_cmd.raw)
        except Exception as exc:
            logger.warning("Engine error processing command %r: %s", parsed, exc)
            return asdict(ErrorMessage(reason=str(exc)))

        self.bus.publish("move_made", {"raw": parsed_cmd.raw, "state": self.state})
        return protocol.serialize_state(self.state)
