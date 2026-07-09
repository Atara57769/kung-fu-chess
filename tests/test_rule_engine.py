import pytest
from models.board import Board
from models.pieces import Piece
from models.cell import Cell
from rules.rule_engine import RuleEngine

def test_rule_engine_valid_move():
    # Set up a board with a white king at (0, 0)
    lines = [
        "wK . .",
        ". . .",
        ". . ."
    ]
    board = Board(lines)
    cell_from = Cell(0, 0)
    
    engine = RuleEngine()
    
    # 1. Test move within bounds, valid for King (moving diagonally to (1, 1))
    cell_to = Cell(1, 1)
    assert engine.is_move_valid(board, cell_from, cell_to) is True
    
    # 2. Test outside board (out of bounds destination)
    cell_out = Cell(-1, 0)
    assert engine.outside_board(board, cell_from, cell_out) is True
    assert engine.is_move_valid(board, cell_from, cell_out) is False

    # Test outside board (out of bounds source)
    assert engine.outside_board(board, cell_out, cell_to) is True
    assert engine.is_move_valid(board, cell_out, cell_to) is False

    # 3. Test empty source
    cell_empty = Cell(0, 1) # empty cell
    assert engine.empty_source(board, cell_empty) is True
    assert engine.is_move_valid(board, cell_empty, cell_to) is False

    # 4. Test friendly distribution (destination has a friendly piece vs enemy piece vs empty)
    lines_with_pieces = [
        "wK wP bP",
        ". . .",
        ". . ."
    ]
    board_pieces = Board(lines_with_pieces)
    cell_k = Cell(0, 0)
    
    # Destination (0, 1) has friendly pawn 'wP'
    cell_friendly = Cell(0, 1)
    assert engine.friendly_destination(board_pieces, cell_k, cell_friendly) is True
    assert engine.is_move_valid(board_pieces, cell_k, cell_friendly) is False
    
    # Destination (0, 2) has enemy pawn 'bP'
    cell_enemy = Cell(0, 2)
    assert engine.friendly_destination(board_pieces, cell_k, cell_enemy) is False
    # King cannot move two cells horizontally normally, so rule validation check (illegal_to_move) will still be False
    assert engine.is_move_valid(board_pieces, cell_k, cell_enemy) is False

    # 5. Test piece rule check (illegal to move check)
    # White King moving 1 cell right to (0, 1) when it is empty is legal
    lines_empty_dest = [
        "wK . bP",
        ". . .",
        ". . ."
    ]
    board_empty = Board(lines_empty_dest)
    cell_k_empty = Cell(0, 0)
    cell_one_right = Cell(0, 1)
    assert engine.illegal_to_move(board_empty, cell_k_empty, cell_one_right) is True
    assert engine.is_move_valid(board_empty, cell_k_empty, cell_one_right) is True
    
    # White King moving 2 cells right is illegal for King rule
    cell_two_right = Cell(0, 2)
    assert engine.illegal_to_move(board_empty, cell_k_empty, cell_two_right) is False
    assert engine.is_move_valid(board_empty, cell_k_empty, cell_two_right) is False


def test_rule_engine_edge_cases():
    lines = [
        "wK . .",
        ". . .",
        ". . ."
    ]
    board = Board(lines)
    engine = RuleEngine()
    
    # None parameters handling
    assert engine.outside_board(board, None, Cell(0, 0)) is True
    assert engine.outside_board(board, Cell(0, 0), None) is True
    assert engine.empty_source(board, None) is True
    assert engine.friendly_destination(board, None, Cell(0, 0)) is False
    assert engine.friendly_destination(board, Cell(0, 0), None) is False
    assert engine.illegal_to_move(board, None, Cell(0, 0)) is False
    assert engine.illegal_to_move(board, Cell(0, 0), None) is False
    
    # Out of bounds cell handling
    cell_out = Cell(-1, 0)
    assert engine.empty_source(board, cell_out) is True
    assert engine.friendly_destination(board, cell_out, Cell(0, 0)) is False
    assert engine.friendly_destination(board, Cell(0, 0), cell_out) is False
    assert engine.illegal_to_move(board, cell_out, Cell(0, 0)) is False
    
    # Empty source piece checks
    cell_empty = Cell(0, 1)
    assert engine.friendly_destination(board, cell_empty, Cell(0, 0)) is False
    assert engine.illegal_to_move(board, cell_empty, Cell(0, 0)) is False
    
    # Piece with invalid/unknown kind
    bad_piece = Piece("w", "X", Cell(0, 0))
    board.grid[0][0] = bad_piece
    assert engine.illegal_to_move(board, Cell(0, 0), Cell(1, 1)) is False
