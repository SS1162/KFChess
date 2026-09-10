import constants
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


@dataclass(frozen=True)
class JoinRequest:
    username: str
    password: str
    type: Literal["join"] = field(default="join")


@dataclass(frozen=True)
class JoinAck:
    username: str
    color: Literal[constants.WHITE, constants.BLACK]
    elo: int
    type: Literal["joined"] = field(default="joined")


def parse_join(raw_dict: dict) -> JoinRequest:
    if not isinstance(raw_dict, dict):
        raise ProtocolError(f"Expected a dict, got: {raw_dict!r}")
    if raw_dict.get("type") != "join":
        raise ProtocolError(f"Expected type 'join', got: {raw_dict.get('type')!r}")
    username = raw_dict.get("username")
    if not isinstance(username, str) or not username.strip():
        raise ProtocolError(f"Invalid or missing username: {username!r}")
    password = raw_dict.get("password")
    if not isinstance(password, str) or not password.strip():
        raise ProtocolError(f"Invalid or missing password: {password!r}")
    return JoinRequest(username=username, password=password)


def parse_incoming(parsed: dict) -> IncomingCommand:
    if not isinstance(parsed, dict) or parsed.get("type") != "command":
        raise ProtocolError(f"Expected type 'command', got: {parsed!r}")
    raw = parsed.get("raw")
    if not isinstance(raw, str) or not raw.strip():
        raise ProtocolError(f"Invalid or missing raw command: {raw!r}")
    return IncomingCommand(raw=raw)


def serialize_state(state: GameState) -> Dict:
    return asdict(StateUpdate(
        board=[row[:] for row in state.board.grid],
        status=state.status.name,
    ))
