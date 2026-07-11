import io
from services.board_printer import print_board
from services.board_parser import TextBoardParser
from factory import PieceFactory

def test_print_piece():
    p = PieceFactory.from_text("wK")
    assert PieceFactory.to_text(p) == "wK"
    assert PieceFactory.to_text(None) == "."

def test_print_board():
    board = TextBoardParser().parse(["wK . bP", ". wQ ."])
    output = io.StringIO()
    print_board(board, stdout=output)
    assert output.getvalue() == "wK . bP\n. wQ .\n"
