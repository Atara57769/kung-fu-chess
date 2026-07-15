import pytest
from models.pieces import Piece
from rules.piece_rules import RULES
from models.cell import Cell
from models.board import Board
from services.board_parser import TextBoardParser

def test_from_text():
    assert Piece.from_text(".") is None
    assert Piece.from_text("w") is None
    assert Piece.from_text("wZ") is None
    
    piece = Piece.from_text("wK", Cell(1, 1))
    assert isinstance(piece, Piece)
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(1, 1)

    piece2 = Piece.from_text("bQ")
    assert piece2.color == "b"
    assert piece2.kind == "Q"
    assert piece2.cell is None

def test_piece_base_properties():
    piece = Piece("w", "K", Cell(0, 0))
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(0, 0)

def test_king_moves():
    board = TextBoardParser().parse([
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
    board_clear = TextBoardParser().parse([
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

    board_blocked_h = TextBoardParser().parse([
        ". . .",
        "wP wP wR",
        ". . ."
    ])
    assert rule.is_move_valid(board_blocked_h, Cell(1, 2), Cell(1, 0)) is False

    board_blocked_v = TextBoardParser().parse([
        ". bP .",
        ". bP .",
        ". wR ."
    ])
    assert rule.is_move_valid(board_blocked_v, Cell(2, 1), Cell(0, 1)) is False

def test_bishop_moves():
    board_clear = TextBoardParser().parse([
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

    board_large_blocked = TextBoardParser().parse([
        ". . . .",
        ". bP . .",
        ". . wB .",
        ". . . ."
    ])
    assert rule.is_move_valid(board_large_blocked, Cell(2, 2), Cell(0, 0)) is False

def test_queen_moves():
    board = TextBoardParser().parse([
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
    board = TextBoardParser().parse([
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
    board_w = TextBoardParser().parse([
        ". . .",
        ". . .",
        ". . .",
        ". wP .",
        ". . ."
    ])
    rule = RULES["P"]
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(2, 1)) is True
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(1, 1)) is True

    board_w_blocked = TextBoardParser().parse([
        ". . .",
        ". . .",
        ". bP .",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(1, 1)) is False
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(2, 1)) is False

    board_w_capture = TextBoardParser().parse([
        ". . .",
        ". . .",
        "bP . bP",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 0)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 2)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 1)) is True

    board_w_diag_empty = TextBoardParser().parse([
        ". . .",
        ". . .",
        ". . .",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_diag_empty, Cell(3, 1), Cell(2, 0)) is False

    board_w_small = TextBoardParser().parse([
        ". . .",
        ". . .",
        ". wP .",
        ". . ."
    ])
    assert rule.is_move_valid(board_w_small, Cell(2, 1), Cell(0, 1)) is True

    board_b = TextBoardParser().parse([
        ". . .",
        ". bP .",
        ". . .",
        ". . .",
        ". . ."
    ])
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(2, 1)) is True
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(3, 1)) is True

    board_b_small = TextBoardParser().parse([
        ". . .",
        ". bP .",
        ". . .",
        ". . ."
    ])
    assert rule.is_move_valid(board_b_small, Cell(1, 1), Cell(3, 1)) is True

    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 1)) is False
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 2)) is False
    assert rule.is_move_valid(board_b, Cell(2, 1), Cell(4, 1)) is False


def test_moving_pieces_do_not_block_paths():
    board = TextBoardParser().parse([
        "wR . wP .",
    ])
    rule = RULES["R"]
    assert rule.is_move_valid(board, Cell(0, 0), Cell(0, 3)) is False
    
    blocker = board.get_piece_at(Cell(0, 2))
    from models.pieces import PieceStatus
    blocker.status = PieceStatus.MOVING
    assert rule.is_move_valid(board, Cell(0, 0), Cell(0, 3)) is True


def test_moving_pieces_do_not_block_pawn_double_step():
    board = TextBoardParser().parse([
        ". . .",
        ". . .",
        ". bP .",
        ". wP .",
        ". . ."
    ])
    rule = RULES["P"]
    assert rule.is_move_valid(board, Cell(3, 1), Cell(1, 1)) is False
    
    blocker = board.get_piece_at(Cell(2, 1))
    from models.pieces import PieceStatus
    blocker.status = PieceStatus.MOVING
    assert rule.is_move_valid(board, Cell(3, 1), Cell(1, 1)) is True
