import logging

logger = logging.getLogger(__name__)


def log_move(data: dict) -> None:
    """Subscriber for the 'move_made' bus event. Logs the move at INFO
    level to the project's standard logger (kfchess.log)."""
    logger.info("Move played: %s", data["raw"])
