from board import Board


def test_str_formats_rows_with_space_separated_tokens():
    board = Board(rows=2, cols=3, grid=[['wK', '.', 'bQ'], ['.', 'wN', '.']])
    assert str(board) == "wK . bQ\n. wN ."
