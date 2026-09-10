from board import Board
from exceptions import BoardError
from game_state import GameState
from parser import TextBoardParser
from validator import BoardValidator


def load_game_state(board_path: str) -> GameState:
    with open(board_path) as f:
        grid, _ = TextBoardParser().parse(f)
    BoardValidator.validate(grid)
    return GameState(board=Board(rows=len(grid), cols=len(grid[0]), grid=grid))
