import io
from output.board_printer import print_piece, print_board
from models.pieces import PieceFactory
from models.board import Board

def test_print_piece():
    p = PieceFactory.get_piece("wK")
    assert print_piece(p) == "wK"
    assert print_piece(None) == "."

def test_print_board():
    board = Board(["wK . bP", ". wQ ."])
    output = io.StringIO()
    print_board(board, stdout=output)
    assert output.getvalue() == "wK . bP\n. wQ .\n"
