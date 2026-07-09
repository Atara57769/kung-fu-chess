import pytest
from models.pieces import get_piece, Piece, King, Rook, Bishop, Queen, Knight, Pawn
from models.cell import Cell
from constants import DURATION

# Mock board structure for tests
class MockBoard:
    def __init__(self, grid):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

def test_get_piece():
    assert get_piece(".") is None
    assert get_piece("w") is None
    assert get_piece("wZ") is None
    assert isinstance(get_piece("wK"), King)
    assert get_piece("wK").color == "w"
    assert get_piece("bQ").name == "Q"

def test_piece_base_properties():
    # Concrete piece for base properties test
    piece = King("w")
    assert piece.token == "wK"
    assert DURATION == 1000
    assert piece.is_king is True
    assert piece.is_pawn is False

    pawn = Pawn("b")
    assert pawn.is_king is False
    assert pawn.is_pawn is True
    
    # Assert name properties for all classes
    assert get_piece("wR").name == "R"
    assert get_piece("wB").name == "B"
    assert get_piece("wN").name == "N"
    assert get_piece("wP").name == "P"
    assert get_piece("wQ").name == "Q"

def test_king_moves():
    board = MockBoard([
        [".", ".", "."],
        [".", "wK", "."],
        [".", ".", "."]
    ])
    king = get_piece("wK")
    assert king.is_legal_move(board, Cell(1, 1), Cell(0, 0)) is True
    assert king.is_legal_move(board, Cell(1, 1), Cell(0, 1)) is True
    assert king.is_legal_move(board, Cell(1, 1), Cell(1, 2)) is True
    assert king.is_legal_move(board, Cell(1, 1), Cell(1, 1)) is False  # (0, 0) move
    assert king.is_legal_move(board, Cell(1, 1), Cell(1, 3)) is False  # too far

def test_rook_moves():
    # Path is clear
    board_clear = MockBoard([
        [".", ".", "."],
        [".", "wR", "."],
        [".", ".", "."]
    ])
    rook = get_piece("wR")
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(1, 2)) is True  # right
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(1, 0)) is True  # left
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(0, 1)) is True  # up
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(2, 1)) is True  # down
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(0, 0)) is False  # diagonal
    assert rook.is_legal_move(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    # Path is blocked horizontally
    board_blocked_h = MockBoard([
        [".", ".", "."],
        ["wP", "wP", "wR"],
        [".", ".", "."]
    ])
    assert rook.is_legal_move(board_blocked_h, Cell(1, 2), Cell(1, 0)) is False

    # Path is blocked vertically
    board_blocked_v = MockBoard([
        [".", "bP", "."],
        [".", "bP", "."],
        [".", "wR", "."]
    ])
    assert rook.is_legal_move(board_blocked_v, Cell(2, 1), Cell(0, 1)) is False

def test_bishop_moves():
    board_clear = MockBoard([
        [".", ".", "."],
        [".", "wB", "."],
        [".", ".", "."]
    ])
    bishop = get_piece("wB")
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(0, 0)) is True
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(0, 2)) is True
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(2, 0)) is True
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(2, 2)) is True
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(1, 2)) is False  # orthogonal
    assert bishop.is_legal_move(board_clear, Cell(1, 1), Cell(1, 1)) is False  # stay

    # Blocked diagonal path
    board_blocked = MockBoard([
        ["bP", ".", "."],
        [".", "wB", "."],
        [".", ".", "."]
    ])
    # Note: path clear checks excluding endpoints, so from (1, 1) to (0, 0) has no intermediate cell,
    # so we need a larger board to test blocked diagonal intermediate cell.
    board_large_blocked = MockBoard([
        [".", ".", ".", "."],
        [".", "bP", ".", "."],
        [".", ".", "wB", "."],
        [".", ".", ".", "."]
    ])
    assert bishop.is_legal_move(board_large_blocked, Cell(2, 2), Cell(0, 0)) is False

def test_queen_moves():
    board = MockBoard([
        [".", ".", ".", "."],
        [".", "wQ", ".", "."],
        [".", ".", ".", "."],
        [".", ".", ".", "."]
    ])
    queen = get_piece("wQ")
    assert queen.is_legal_move(board, Cell(1, 1), Cell(1, 3)) is True  # straight
    assert queen.is_legal_move(board, Cell(1, 1), Cell(3, 3)) is True  # diagonal
    assert queen.is_legal_move(board, Cell(1, 1), Cell(3, 2)) is False  # L-shape
    assert queen.is_legal_move(board, Cell(1, 1), Cell(1, 1)) is False  # stay

def test_knight_moves():
    board = MockBoard([
        [".", ".", ".", "."],
        [".", "wN", ".", "."],
        [".", ".", ".", "."],
        [".", ".", ".", "."]
    ])
    knight = get_piece("wN")
    assert knight.is_legal_move(board, Cell(1, 1), Cell(3, 2)) is True  # L-shape
    assert knight.is_legal_move(board, Cell(1, 1), Cell(2, 3)) is True  # L-shape
    assert knight.is_legal_move(board, Cell(1, 1), Cell(1, 3)) is False  # horizontal
    assert knight.is_legal_move(board, Cell(1, 1), Cell(1, 1)) is False

def test_pawn_moves():
    # White Pawn - large board (H >= 5)
    # y Cells: 0, 1, 2, 3, 4. start_row = H - 2 = 3. expected_dy = -1
    board_w = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    pawn_w = get_piece("wP")
    # Single step forward to empty
    assert pawn_w.is_legal_move(board_w, Cell(3, 1), Cell(2, 1)) is True
    # Double step forward from start_row to empty
    assert pawn_w.is_legal_move(board_w, Cell(3, 1), Cell(1, 1)) is True

    # Blocked double step (intermediate blocked)
    board_w_blocked = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", "bP", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert pawn_w.is_legal_move(board_w_blocked, Cell(3, 1), Cell(1, 1)) is False

    # Blocked single step
    assert pawn_w.is_legal_move(board_w_blocked, Cell(3, 1), Cell(2, 1)) is False

    # Capture move
    board_w_capture = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        ["bP", ".", "bP"],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert pawn_w.is_legal_move(board_w_capture, Cell(3, 1), Cell(2, 0)) is True  # capture left
    assert pawn_w.is_legal_move(board_w_capture, Cell(3, 1), Cell(2, 2)) is True  # capture right
    assert pawn_w.is_legal_move(board_w_capture, Cell(3, 1), Cell(2, 1)) is True  # step to empty

    # Diagonal move to empty (illegal)
    board_w_diag_empty = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
        [".", ".", "."]
    ])
    assert pawn_w.is_legal_move(board_w_diag_empty, Cell(3, 1), Cell(2, 0)) is False

    # White Pawn - small board (H = 3, H < 5). start_row = H - 1 = 2.
    board_w_small = MockBoard([
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."]
    ])
    # Expected start_row is 2. Let's do double step from 2. expected_dy = -1, 2 * expected_dy = -2. Target row 0.
    assert pawn_w.is_legal_move(board_w_small, Cell(2, 1), Cell(0, 1)) is True

    # Black Pawn - large board (H >= 5). start_row = 1. expected_dy = 1
    board_b = MockBoard([
        [".", ".", "."],
        [".", "bP", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."]
    ])
    pawn_b = get_piece("bP")
    assert pawn_b.is_legal_move(board_b, Cell(1, 1), Cell(2, 1)) is True  # single step
    assert pawn_b.is_legal_move(board_b, Cell(1, 1), Cell(3, 1)) is True  # double step

    # Black Pawn - small board (H = 3, H < 5). start_row = 0.
    board_b_small = MockBoard([
        [".", "bP", "."],
        [".", ".", "."],
        [".", ".", "."]
    ])
    assert pawn_b.is_legal_move(board_b_small, Cell(0, 1), Cell(2, 1)) is True  # double step

    # Other illegal moves
    assert pawn_b.is_legal_move(board_b, Cell(1, 1), Cell(1, 1)) is False  # stay
    assert pawn_b.is_legal_move(board_b, Cell(1, 1), Cell(1, 2)) is False  # horizontal
    assert pawn_b.is_legal_move(board_b, Cell(2, 1), Cell(4, 1)) is False  # double step from non-start row
