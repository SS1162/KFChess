from command_executor import CommandExecutor
from commands import ClickCommand, JumpCommand, PrintBoardCommand, WaitCommand
from handlers.click import ClickCommandHandler, parse_click
from handlers.jump import handle_jump, parse_jump
from handlers.print_board import handle_print_board, parse_print
from handlers.wait import handle_wait, parse_wait
from movement import (MoveValidator, bishop_can_move, king_can_move,
                      knight_can_move, pawn_can_move, queen_can_move,
                      rook_can_move)
from parser import CommandParser


def build_move_validator() -> MoveValidator:
    mv = MoveValidator()
    mv.register('K', king_can_move)
    mv.register('Q', queen_can_move)
    mv.register('R', rook_can_move)
    mv.register('B', bishop_can_move)
    mv.register('N', knight_can_move)
    mv.register('P', pawn_can_move)
    return mv


def build_command_parser() -> CommandParser:
    cp = CommandParser()
    cp.register("click", parse_click)
    cp.register("jump",  parse_jump)
    cp.register("wait",  parse_wait)
    cp.register("print", parse_print)
    return cp


def build_executor() -> CommandExecutor:
    move_validator = build_move_validator()
    click_handler  = ClickCommandHandler(move_validator)
    ex = CommandExecutor()
    ex.register(ClickCommand,      click_handler.execute)
    ex.register(JumpCommand,        handle_jump)
    ex.register(WaitCommand,        handle_wait)
    ex.register(PrintBoardCommand,  handle_print_board)
    return ex
