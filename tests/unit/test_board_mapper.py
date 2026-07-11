import pytest
from models.board import Board
from models.cell import Cell
from input.board_mappr import BoardMapper
from services.board_parser import TextBoardParser

def test_board_mapper_pixel_to_cell_valid():
    board = TextBoardParser().parse([
        "wK .",
        ". bP"
    ])
    mapper = BoardMapper(board)
    
    assert mapper.pixel_to_cell(50, 50) == Cell(y=0, x=0)
    assert mapper.pixel_to_cell(150, 50) == Cell(y=0, x=1)
    assert mapper.pixel_to_cell(50, 150) == Cell(y=1, x=0)
    assert mapper.pixel_to_cell(150, 150) == Cell(y=1, x=1)

def test_board_mapper_pixel_to_cell_out_of_bounds():
    board = TextBoardParser().parse([
        "wK .",
        ". bP"
    ])
    mapper = BoardMapper(board)
    
    assert mapper.pixel_to_cell(-10, 50) is None
    assert mapper.pixel_to_cell(50, -10) is None
    assert mapper.pixel_to_cell(-5, -5) is None
    
    assert mapper.pixel_to_cell(200, 50) is None
    assert mapper.pixel_to_cell(50, 200) is None
    assert mapper.pixel_to_cell(250, 250) is None
