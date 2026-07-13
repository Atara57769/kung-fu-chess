from models.cell import Cell
from models.pieces import Piece
from models.pending_move import PendingMove
from constants import COLOR_WHITE, PIECE_ROOK, PIECE_KNIGHT, PIECE_BISHOP

def test_pending_move_knight():
    piece = Piece(COLOR_WHITE, PIECE_KNIGHT)
    move = PendingMove(Cell(0, 0), Cell(2, 1), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(2, 1)]

def test_pending_move_horizontal():
    piece = Piece(COLOR_WHITE, PIECE_ROOK)
    move = PendingMove(Cell(0, 0), Cell(0, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(0, 1), Cell(0, 2), Cell(0, 3)]

def test_pending_move_vertical():
    piece = Piece(COLOR_WHITE, PIECE_ROOK)
    move = PendingMove(Cell(0, 0), Cell(3, 0), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(1, 0), Cell(2, 0), Cell(3, 0)]

def test_pending_move_diagonal():
    piece = Piece(COLOR_WHITE, PIECE_BISHOP)
    move = PendingMove(Cell(0, 0), Cell(3, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(1, 1), Cell(2, 2), Cell(3, 3)]

def test_pending_move_stationary():
    piece = Piece(COLOR_WHITE, PIECE_ROOK)
    move = PendingMove(Cell(1, 1), Cell(1, 1), piece, 1000)
    assert move.path == [Cell(1, 1)]

def test_pending_move_predefined_path():
    piece = Piece(COLOR_WHITE, PIECE_ROOK)
    custom_path = [Cell(1, 1), Cell(2, 2)]
    move = PendingMove(Cell(0, 0), Cell(3, 3), piece, 1000)
    move.path = custom_path
    assert move.path == custom_path

def test_pending_move_non_straight():
    piece = Piece(COLOR_WHITE, PIECE_ROOK)
    move = PendingMove(Cell(0, 0), Cell(2, 3), piece, 1000)
    assert move.path == [Cell(0, 0), Cell(2, 3)]
