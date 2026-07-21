import io
from server.game.services.board_printer import print_board
from server.game.services.board_parser import TextBoardParser
from shared.models.pieces import Piece

def test_print_piece():
    p = Piece.from_text("wK")
    assert Piece.to_text(p) == "wK"
    assert Piece.to_text(None) == "."

def test_print_board():
    board = TextBoardParser().parse(["wK . bP", ". wQ ."])
    output = io.StringIO()
    print_board(board, stdout=output)
    assert output.getvalue() == "wK . bP\n. wQ .\n"
