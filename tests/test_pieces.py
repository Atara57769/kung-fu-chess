import pytest
from models.pieces import PieceFactory, Piece
get_piece = PieceFactory.get_piece
from rules.piece_rules import RULES, RookRule, BishopRule, QueenRule, KnightRule, KingRule, PawnRule
from models.cell import Cell

# Mock board structure for tests
class MockBoard:
    def __init__(self, grid):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

    def get_piece_at(self, cell_y: int, cell_x: int):
        token = self.grid[cell_y][cell_x]
        return get_piece(token, Cell(cell_y, cell_x))

def test_get_piece():
    assert get_piece(".") is None
    assert get_piece("w") is None
    assert get_piece("wZ") is None
    
    piece = get_piece("wK", Cell(1, 1))
    assert isinstance(piece, Piece)
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(1, 1)

    piece2 = get_piece("bQ")
    assert piece2.color == "b"
    assert piece2.kind == "Q"
    assert piece2.cell is None

def test_piece_base_properties():
    piece = Piece("w", "K", Cell(0, 0))
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell == Cell(0, 0)

def test_king_moves():
    board = MockBoard([
        [".", ".", "."],
        [".", "wK", "."],
        [".", ".", "."]
    ])
    rule = RULES["K"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(0, 0)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(0, 1)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 2)) is True
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False  # (0, 0) move
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is False  # too far

def test_rook_moves():
    # Path is clear
    board_clear = MockBoard([
        [".", ".", "."],
        [".", "wR", "."],
        [".", ".", "."]
    ])
    rule = RULES["R"]
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 2)) is True  # right
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 0)) is True  # left
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 1)) is True  # up
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 1)) is True  # down
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 0)) is False  # diagonal
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    # Path is blocked horizontally
    board_blocked_h = MockBoard([
        [".", ".", "."],
        ["wP", "wP", "wR"],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_blocked_h, Cell(1, 2), Cell(1, 0)) is False

    # Path is blocked vertically
    board_blocked_v = MockBoard([
        [".", "bP", "."],
        [".", "bP", "."],
        [".", "wR", "."]
    ])
    assert rule.is_move_valid(board_blocked_v, Cell(2, 1), Cell(0, 1)) is False

def test_bishop_moves():
    board_clear = MockBoard([
        [".", ".", "."],
        [".", "wB", "."],
        [".", ".", "."]
    ])
    rule = RULES["B"]
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 0)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(0, 2)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 0)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(2, 2)) is True
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 2)) is False  # orthogonal
    assert rule.is_move_valid(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    # Blocked diagonal path
    board_blocked = MockBoard([
        ["bP", ".", "."],
        [".", "wB", "."],
        [".", ".", "."]
    ])
    board_large_blocked = MockBoard([
        [".", ".", ".", "."],
        [".", "bP", ".", "."],
        [".", ".", "wB", "."],
        [".", ".", ".", "."]
    ])
    assert rule.is_move_valid(board_large_blocked, Cell(2, 2), Cell(0, 0)) is False

def test_queen_moves():
    board = MockBoard([
        [".", ".", ".", "."],
        [".", "wQ", ".", "."],
        [".", ".", ".", "."],
        [".", ".", ".", "."]
    ])
    rule = RULES["Q"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is True  # straight
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 3)) is True  # diagonal
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 2)) is False  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False  # stay

def test_knight_moves():
    board = MockBoard([
        [".", ".", ".", "."],
        [".", "wN", ".", "."],
        [".", ".", ".", "."],
        [".", ".", ".", "."]
    ])
    rule = RULES["N"]
    assert rule.is_move_valid(board, Cell(1, 1), Cell(3, 2)) is True  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(2, 3)) is True  # L-shape
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 3)) is False  # horizontal
    assert rule.is_move_valid(board, Cell(1, 1), Cell(1, 1)) is False

def test_pawn_moves():
    board_w = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    rule = RULES["P"]
    # Single step forward to empty
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(2, 1)) is True
    # Double step forward from start_row to empty
    assert rule.is_move_valid(board_w, Cell(3, 1), Cell(1, 1)) is True

    # Blocked double step
    board_w_blocked = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", "bP", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(1, 1)) is False

    # Blocked single step
    assert rule.is_move_valid(board_w_blocked, Cell(3, 1), Cell(2, 1)) is False

    # Capture move
    board_w_capture = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        ["bP", ".", "bP"],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 0)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 2)) is True
    assert rule.is_move_valid(board_w_capture, Cell(3, 1), Cell(2, 1)) is True

    # Diagonal move to empty
    board_w_diag_empty = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_w_diag_empty, Cell(3, 1), Cell(2, 0)) is False

    # White Pawn - small board (H = 3)
    board_w_small = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."]
    ])
    assert rule.is_move_valid(board_w_small, Cell(2, 1), Cell(0, 1)) is True

    # Black Pawn - large board
    board_b = MockBoard([
        [".", ".", "."],
        [".", "bP", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(2, 1)) is True
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(3, 1)) is True

    # Black Pawn - small board
    board_b_small = MockBoard([
        [".", "bP", "."],
        [".", ".", "."],
        [".", ".", "."]
    ])
    assert rule.is_move_valid(board_b_small, Cell(0, 1), Cell(2, 1)) is True

    # Other illegal moves
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 1)) is False
    assert rule.is_move_valid(board_b, Cell(1, 1), Cell(1, 2)) is False
    assert rule.is_move_valid(board_b, Cell(2, 1), Cell(4, 1)) is False
