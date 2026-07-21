from shared.models.cell import Cell
from shared.models.pieces import Piece
from shared.models.pending_move import PendingMove
from shared.models.color import Color
from shared.models.piece_type import PieceType

def test_pending_move_knight():
    piece = Piece(Color.WHITE, PieceType.KNIGHT)
    move = PendingMove(Cell(0, 0), Cell(2, 1), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(2, 1)]

def test_pending_move_horizontal():
    piece = Piece(Color.WHITE, PieceType.ROOK)
    move = PendingMove(Cell(0, 0), Cell(0, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(0, 1), Cell(0, 2), Cell(0, 3)]

def test_pending_move_vertical():
    piece = Piece(Color.WHITE, PieceType.ROOK)
    move = PendingMove(Cell(0, 0), Cell(3, 0), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(1, 0), Cell(2, 0), Cell(3, 0)]

def test_pending_move_diagonal():
    piece = Piece(Color.WHITE, PieceType.BISHOP)
    move = PendingMove(Cell(0, 0), Cell(3, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(1, 1), Cell(2, 2), Cell(3, 3)]

def test_pending_move_stationary():
    piece = Piece(Color.WHITE, PieceType.ROOK)
    move = PendingMove(Cell(1, 1), Cell(1, 1), piece, 1000)
    assert move.path == [Cell(1, 1)]

def test_pending_move_predefined_path():
    piece = Piece(Color.WHITE, PieceType.ROOK)
    custom_path = [Cell(1, 1), Cell(2, 2)]
    move = PendingMove(Cell(0, 0), Cell(3, 3), piece, 1000)
    move.path = custom_path
    assert move.path == custom_path

def test_pending_move_non_straight():
    piece = Piece(Color.WHITE, PieceType.ROOK)
    move = PendingMove(Cell(0, 0), Cell(2, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(2, 3)]
