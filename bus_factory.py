from bus import Bus
from move_logger import log_move


def build_bus() -> Bus:
    bus = Bus()
    bus.subscribe("move_made", log_move)
    return bus
