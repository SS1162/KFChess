from board import Board


def test_str_formats_rows_with_space_separated_tokens():
    board = Board(rows=2, cols=3, grid=[['wK', '.', 'bQ'], ['.', 'wN', '.']])
    assert str(board) == "wK . bQ\n. wN ."


def test_get_token_returns_correct_cell():
    board = Board(rows=2, cols=2, grid=[['wK', '.'], ['.', 'bQ']])
    assert board.get_token(0, 0) == 'wK'
    assert board.get_token(1, 1) == 'bQ'
    assert board.get_token(0, 1) == '.'
