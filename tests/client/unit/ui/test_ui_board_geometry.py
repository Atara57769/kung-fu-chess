import pytest
from shared.models.cell import Cell
from client.ui.board.board_geometry import BoardGeometry

def test_board_geometry_cell_to_pixel():
    geom = BoardGeometry(cell_size=50)
    assert geom.cell_size == 50
    
    assert geom.cell_to_top_left_pixel(Cell(1, 2)) == (100, 50)
    assert geom.cell_to_center_pixel(Cell(1, 2)) == (125, 75)

def test_board_geometry_pixel_to_cell():
    geom = BoardGeometry(cell_size=50)
    
    # Valid cells
    assert geom.pixel_to_cell(120, 80) == Cell(1, 2)
    
    # Negative/invalid coordinates
    assert geom.pixel_to_cell(-1, 50) is None
    assert geom.pixel_to_cell(50, -10) is None
