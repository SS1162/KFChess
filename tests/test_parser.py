from io import StringIO

from parser import TextBoardParser


def test_parses_board_and_commands():
    src = "Board:\nwK . bQ\n. wN .\nCommands:\nprint board\n"
    grid, commands = TextBoardParser().parse(StringIO(src))
    assert grid == [['wK', '.', 'bQ'], ['.', 'wN', '.']]
    assert commands == ['print board']


def test_strips_surrounding_blank_lines_from_board():
    src = "Board:\n\nwK .\n. bK\n\nCommands:\n"
    grid, _ = TextBoardParser().parse(StringIO(src))
    assert grid == [['wK', '.'], ['.', 'bK']]


def test_missing_commands_header_returns_empty_list():
    src = "Board:\nwK .\n. bK\n"
    _, commands = TextBoardParser().parse(StringIO(src))
    assert commands == []
