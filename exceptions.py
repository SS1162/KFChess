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


class CommandError(ValueError):
    """Base exception for all command-parsing and command-argument errors.

    Extends ValueError so CommandParser's catch clause covers it, and so
    callers that previously caught ValueError continue to work.
    """


class UnknownCommandTargetError(CommandError):
    """Raised when a command's target argument is not recognised.

    Attributes:
        command: the keyword that was parsed (e.g. 'print').
        target:  the unrecognised target that followed it (e.g. 'clock').
    """

    def __init__(self, command: str, target: str) -> None:
        self.command = command
        self.target = target
        super().__init__(
            f"Command {command!r} does not support target {target!r}. "
            f"Check the command syntax and available targets."
        )


class InvalidCommandArgumentError(CommandError):
    """Raised when a command argument has a value that is structurally valid
    but logically out of range or otherwise illegal.

    Attributes:
        command:  the command keyword (e.g. 'wait').
        argument: name of the offending argument (e.g. 'ms').
        value:    the actual value that was rejected.
        reason:   human-readable explanation of the constraint.
    """

    def __init__(self, command: str, argument: str, value: object, reason: str) -> None:
        self.command = command
        self.argument = argument
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid value {value!r} for argument '{argument}' of command {command!r}: {reason}"
        )
