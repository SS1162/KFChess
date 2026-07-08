import pytest

from exceptions import EmptyBoardError, IllegalTokenError, InvalidDimensionsError
from validator import BoardValidator

VALID_GRID = [['wK', '.', 'bQ'], ['.', 'wN', '.'], ['bP', '.', 'wR']]


def test_valid_grid_passes():
    BoardValidator.validate(VALID_GRID)  # must not raise


def test_empty_grid_raises():
    with pytest.raises(EmptyBoardError):
        BoardValidator.validate([])


def test_ragged_rows_raises():
    with pytest.raises(InvalidDimensionsError) as exc_info:
        BoardValidator.validate([['wK', '.', '.'], ['.', 'bK']])
    err = exc_info.value
    assert err.row == 1 and err.expected == 3 and err.got == 2
    assert err.error_code == 'ROW_WIDTH_MISMATCH'


def test_unknown_token_raises():
    with pytest.raises(IllegalTokenError) as exc_info:
        BoardValidator.validate([['wK', 'xZ'], ['.', '.']])
    err = exc_info.value
    assert err.token == 'xZ' and err.row == 0
    assert err.error_code == 'UNKNOWN_TOKEN'
