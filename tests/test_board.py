import pytest
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError

def test_board_initialization_valid():
    lines = [
        "wK . bP",
        ". wQ .",
        "wN bB wP"
    ]
    board = Board(lines)
    assert board.width == 3
    assert len(board.grid) == 3
    assert board.grid[0] == ["wK", ".", "bP"]
    assert board.grid[1] == [".", "wQ", "."]
    assert board.grid[2] == ["wN", "bB", "wP"]

def test_board_initialization_empty():
    board = Board([])
    assert board.width == 0
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
