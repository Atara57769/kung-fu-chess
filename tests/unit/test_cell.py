from models.cell import Cell

def test_cell_initialization():
    cell = Cell(y=1, x=2)
    assert cell.y == 1
    assert cell.x == 2

def test_cell_frozen():
    import pytest
    from dataclasses import FrozenInstanceError
    cell = Cell(y=1, x=2)
    with pytest.raises(FrozenInstanceError):
        cell.y = 3
