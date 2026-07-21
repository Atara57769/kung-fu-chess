import pytest
from shared.models.board import Board
from shared.models.cell import Cell
from server.game.services.script_runner import ScriptRunner
from server.game.services.board_parser import TextBoardParser

def test_script_runner_pixel_to_cell_valid():
    board = TextBoardParser().parse([
        "wK .",
        ". bP"
    ])
    runner = ScriptRunner()
    
    assert runner._pixel_to_cell(board, 50, 50) == Cell(y=0, x=0)
    assert runner._pixel_to_cell(board, 150, 50) == Cell(y=0, x=1)
    assert runner._pixel_to_cell(board, 50, 150) == Cell(y=1, x=0)
    assert runner._pixel_to_cell(board, 150, 150) == Cell(y=1, x=1)

def test_script_runner_pixel_to_cell_out_of_bounds():
    board = TextBoardParser().parse([
        "wK .",
        ". bP"
    ])
    runner = ScriptRunner()
    
    assert runner._pixel_to_cell(board, -10, 50) is None
    assert runner._pixel_to_cell(board, 50, -10) is None
    assert runner._pixel_to_cell(board, -5, -5) is None
    
    assert runner._pixel_to_cell(board, 200, 50) is None
    assert runner._pixel_to_cell(board, 50, 200) is None
    assert runner._pixel_to_cell(board, 250, 250) is None
