import pytest
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError

from models.pieces import Piece
from models.cell import Cell

def test_board_initialization_valid():
    lines = [
        "wK . bP",
        ". wQ .",
        "wN bB wP"
    ]
    board = Board(lines)
    assert board.width == 3
    assert board.height == 3
    assert len(board.grid) == 3
    assert board.grid[0] == [Piece("w", "K", Cell(0, 0)), None, Piece("b", "P", Cell(0, 2))]
    assert board.grid[1] == [None, Piece("w", "Q", Cell(1, 1)), None]
    assert board.grid[2] == [Piece("w", "N", Cell(2, 0)), Piece("b", "B", Cell(2, 1)), Piece("w", "P", Cell(2, 2))]

def test_board_initialization_empty():
    board = Board([])
    assert board.width == 0
    assert board.height == 0
    assert board.grid == []

def test_board_unknown_token():
    lines = ["wK . xP"]
    with pytest.raises(UnknownTokenError) as excinfo:
        Board(lines)
    assert "ERROR UNKNOWN_TOKEN" in str(excinfo.value)

    # Token with wrong length
    with pytest.raises(UnknownTokenError):
        Board(["wK . wK2"])

    # Token with wrong color
    with pytest.raises(UnknownTokenError):
        Board(["wK . zP"])

    # Token with wrong piece
    with pytest.raises(UnknownTokenError):
        Board(["wK . wZ"])

def test_board_row_width_mismatch():
    lines = [
        "wK .",
        "bP . bB ."
    ]
    with pytest.raises(RowWidthMismatchError) as excinfo:
        Board(lines)
    assert "ERROR ROW_WIDTH_MISMATCH" in str(excinfo.value)
