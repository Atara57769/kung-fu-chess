import pytest
from models.pieces import PieceFactory, Piece
from rules.piece_rules import RULES
from models.cell import Cell
from models.board import Board

def test_get_piece():
    assert PieceFactory.get_piece(".") is None
    assert PieceFactory.get_piece("w") is None
    assert PieceFactory.get_piece("wZ") is None
    
    piece = PieceFactory.get_piece("wK", Cell(1, 1))
    assert isinstance(piece, Piece)
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(1, 1)

    piece2 = PieceFactory.get_piece("bQ")
    assert piece2.color == "b"
    assert piece2.kind == "Q"
    assert piece2.cell is None

def test_piece_base_properties():
    piece = Piece("w", "K", Cell(0, 0))
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(0, 0)

def test_king_moves():
    board = Board([
        ". . .",
        ". wK .",
        ". . ."
    ])
    rule = RULES["K"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(0, 0)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(0, 1)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 2)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False  # stay
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is False  # too far

def test_rook_moves():
    board_clear = Board([
        ". . .",
        ". wR .",
        ". . ."
    ])
    rule = RULES["R"]
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 2)) is True  # right
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 0)) is True  # left
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 1)) is True  # up
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 1)) is True  # down
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 0)) is False  # diagonal
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    board_blocked_h = Board([
        ". . .",
        "wP wP wR",
        ". . ."
    ])
    assert rule.is_move_valid(board_blocked_h, Cell(1, 2), Cell(1, 0)) is False

    board_blocked_v = Board([
        ". bP .",
        ". bP .",
        ". wR ."
    ])
    assert rule.is_move_valid(board_blocked_v, Cell(2, 1), Cell(0, 1)) is False

def test_bishop_moves():
    board_clear = Board([
        ". . .",
        ". wB .",
        ". . ."
    ])
    rule = RULES["B"]
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 0)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 2)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 0)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 2)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 2)) is False  # orthogonal
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    board_large_blocked = Board([
        ". . . .",
        ". bP . .",
        ". . wB .",
        ". . . ."
    ])
    assert rule.is_move_valid(board_large_blocked, Cell(2, 2), Cell(0, 0)) is False

def test_queen_moves():
    board = Board([
        ". . . .",
        ". wQ . .",
        ". . . .",
        ". . . ."
    ])
    rule = RULES["Q"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is True  # straight
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 3)) is True  # diagonal
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 2)) is False  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False  # stay

def test_knight_moves():
    board = Board([
        ". . . .",
        ". wN . .",
        ". . . .",
        ". . . ."
    ])
    rule = RULES["N"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 2)) is True  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(2, 3)) is True  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is False  # horizontal
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False

def test_pawn_moves():
    board_w = Board([
        ". . .",
        ". . .",
        ". . .",
        ". wP .",
        ". . ."
    ])
    rule = RULES["P"]
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(2, 1)) is True
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(1, 1)) is True

    board_w_blocked = Board([
        ". . .",
        ". . .",
        ". bP .",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(1, 1)) is False
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(2, 1)) is False

    board_w_capture = Board([
        ". . .",
        ". . .",
        "bP . bP",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 0)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 2)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 1)) is True

    board_w_diag_empty = Board([
        ". . .",
        ". . .",
        ". . .",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_diag_empty, Cell(3, 1), Cell(2, 0)) is False

    board_w_small = Board([
        ". . .",
        ". . .",
        ". wP ."
    ])
    assert rule.is_move_valid(board_w_small, Cell(2, 1), Cell(0, 1)) is True

    board_b = Board([
        ". . .",
        ". bP .",
        ". . .",
        ". . .",
        ". . ."
    ])
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(2, 1)) is True
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(3, 1)) is True

    board_b_small = Board([
        ". bP .",
        ". . .",
        ". . ."
    ])
    assert rule.is_move_valid(board_b_small, Cell(0, 1), Cell(2, 1)) is True

    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 1)) is False
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 2)) is False
    assert rule.is_move_valid(board_b, Cell(2, 1), Cell(4, 1)) is False
