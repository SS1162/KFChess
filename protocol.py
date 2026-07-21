from dataclasses import asdict, dataclass, field
from typing import Dict, List, Literal

from game_state import GameState


class ProtocolError(Exception):
    pass


@dataclass(frozen=True)
class IncomingCommand:
    raw: str
    type: Literal["command"] = field(default="command")


@dataclass(frozen=True)
class StateUpdate:
    # GameState has no turn/current_player/active_color field — KFChess is
    # real-time with concurrent async moves, so no turn concept exists.
    board: List[List[str]]
    status: str
    type: Literal["state"] = field(default="state")


@dataclass(frozen=True)
class ErrorMessage:
    reason: str
    type: Literal["error"] = field(default="error")


def parse_incoming(raw: str) -> IncomingCommand:
    if not isinstance(raw, str) or not raw.strip():
        raise ProtocolError(f"Invalid incoming message: {raw!r}")
    return IncomingCommand(raw=raw)


def serialize_state(state: GameState) -> Dict:
    return asdict(StateUpdate(
        board=[row[:] for row in state.board.grid],
        status=state.status.name,
    ))
