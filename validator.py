import logging
from typing import List

from config import ALLOWED_TOKENS
from exceptions import EmptyBoardError, IllegalTokenError, InvalidDimensionsError

logger = logging.getLogger(__name__)


class BoardValidator:
    """Validates structural and logical correctness of a raw token grid."""

    @staticmethod
    def validate(grid: List[List[str]]) -> None:
        if not grid:
            logger.warning("Validation failed: grid is empty.")
            raise EmptyBoardError("Board must not be empty.")

        col_count = len(grid[0])
        if col_count == 0:
            logger.warning("Validation failed: first row is empty.")
            raise EmptyBoardError("Board rows must not be empty.")

        for i, row in enumerate(grid):
            if len(row) != col_count:
                logger.warning(
                    "Validation failed: row %d has %d token(s); expected %d.",
                    i, len(row), col_count,
                )
                raise InvalidDimensionsError(row=i, expected=col_count, got=len(row))
            for token in row:
                if token not in ALLOWED_TOKENS:
                    logger.warning(
                        "Validation failed: illegal token %r at row %d.", token, i
                    )
                    raise IllegalTokenError(token=token, row=i)
