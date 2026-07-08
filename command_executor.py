import logging
from typing import Any, Callable, Dict

from game_state import GameState

logger = logging.getLogger(__name__)

_Handler = Callable[[Any, GameState], None]


class CommandExecutor:
    """Registry-based executor: maps command types to handler callables.

    Register a command type with a handler that receives (command, state).
    Adding a new command requires only a new registration — this class never changes.

    Example::
        ex = CommandExecutor()
        ex.register(WaitCommand, handle_wait)
        ex.execute(WaitCommand(ms=500), state)
    """

    def __init__(self) -> None:
        self._handlers: Dict[type, _Handler] = {}

    def register(self, cmd_type: type, handler: _Handler) -> None:
        self._handlers[cmd_type] = handler

    def execute(self, command: Any, state: GameState) -> None:
        handler = self._handlers.get(type(command))
        if handler is None:
            logger.warning("No handler registered for %s — command ignored.", type(command).__name__)
            return
        handler(command, state)
