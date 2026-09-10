import pytest
from board import Board


def test_str_formats_rows_with_space_separated_tokens():
    board = Board(rows=2, cols=3, grid=[['wK', '.', 'bQ'], ['.', 'wN', '.']])
    assert str(board) == "wK . bQ\n. wN ."


@pytest.mark.parametrize("row,col,expected", [
    (0, 0, 'wK'),
    (1, 1, 'bQ'),
    (0, 1, '.'),
])
def test_get_token_returns_correct_cell(row, col, expected):
    board = Board(rows=2, cols=2, grid=[['wK', '.'], ['.', 'bQ']])
    assert board.get_token(row, col) == expected
