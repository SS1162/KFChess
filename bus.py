import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)


class Bus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[dict], None]) -> None:
        self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, data: dict) -> None:
        for callback in self._subscribers.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                logger.warning("Callback %s raised an exception for event '%s': %s", callback, event_name, e)
