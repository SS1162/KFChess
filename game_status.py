from enum import Enum, auto
from typing import Dict, Optional


class GameStatus(Enum):
    PLAYING = auto()
    WHITE_WON = auto()
    BLACK_WON = auto()
    DRAW = auto()


class GameOverRegistry:
    """Maps a captured token to the GameStatus it triggers.

    Follows the registry pattern so future game-ending pieces can be added
    without touching any other module.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, GameStatus] = {}

    def register(self, token: str, result: GameStatus) -> None:
        self._rules[token] = result

    def resolve(self, captured_token: str) -> Optional[GameStatus]:
        """Return the resulting GameStatus if capturing this token ends the game, else None."""
        return self._rules.get(captured_token)


default_registry = GameOverRegistry()
default_registry.register('wK', GameStatus.BLACK_WON)
default_registry.register('bK', GameStatus.WHITE_WON)
