class BoardError(ValueError):
    """Base exception for all board-related errors."""
    error_code: str = "BOARD_ERROR"


class EmptyBoardError(BoardError):
    """Raised when the board contains no data."""
    error_code = "EMPTY_BOARD"


class InvalidDimensionsError(BoardError):
    """Raised when rows have inconsistent token counts."""
    error_code = "ROW_WIDTH_MISMATCH"

    def __init__(self, row: int, expected: int, got: int) -> None:
        self.row = row
        self.expected = expected
        self.got = got
        super().__init__(
            f"Row {row} has {got} token(s); expected {expected}."
        )


class IllegalTokenError(BoardError):
    """Raised when a token is not part of the allowed set."""
    error_code = "UNKNOWN_TOKEN"

    def __init__(self, token: str, row: int) -> None:
        self.token = token
        self.row = row
        super().__init__(f"Illegal token {token!r} at row {row}.")
