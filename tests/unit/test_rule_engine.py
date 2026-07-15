import pytest
from models.board import Board
from services.board_parser import TextBoardParser
from models.pieces import Piece
from models.cell import Cell
from rules.rule_engine import RuleEngine
from models.pending_move import PendingMove

def test_rule_engine_valid_move():
    lines = [
        "wK . .",
        ". . .",
        ". . ."
    ]
    board = TextBoardParser().parse(lines)
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
    cell_empty = Cell(0, 1)
    assert engine.empty_source(board, cell_empty) is True
    assert engine.is_move_valid(board, cell_empty, cell_to) is False

    # 4. Test friendly distribution (destination has a friendly piece vs enemy piece vs empty)
    lines_with_pieces = [
        "wK wP bP",
        ". . .",
        ". . ."
    ]
    board_pieces = TextBoardParser().parse(lines_with_pieces)
    cell_k = Cell(0, 0)
    
    # Destination (0, 1) has friendly pawn 'wP'
    cell_friendly = Cell(0, 1)
    assert engine.board_rules.friendly_destination(board_pieces, cell_k, cell_friendly) is True
    assert engine.is_move_valid(board_pieces, cell_k, cell_friendly) is False
    
    # Destination (0, 2) has enemy pawn 'bP'
    cell_enemy = Cell(0, 2)
    assert engine.board_rules.friendly_destination(board_pieces, cell_k, cell_enemy) is False
    # King cannot move two cells horizontally normally, so rule validation check will still be False
    assert engine.is_move_valid(board_pieces, cell_k, cell_enemy) is False

    # 5. Test piece rule check (illegal to move check)
    lines_empty_dest = [
        "wK . bP",
        ". . .",
        ". . ."
    ]
    board_empty = TextBoardParser().parse(lines_empty_dest)
    cell_k_empty = Cell(0, 0)
    cell_one_right = Cell(0, 1)
    assert engine.is_piece_move_valid(board_empty, cell_k_empty, cell_one_right) is True
    assert engine.is_move_valid(board_empty, cell_k_empty, cell_one_right) is True
    
    # White King moving 2 cells right is illegal for King rule
    cell_two_right = Cell(0, 2)
    assert engine.is_piece_move_valid(board_empty, cell_k_empty, cell_two_right) is False
    assert engine.is_move_valid(board_empty, cell_k_empty, cell_two_right) is False

def test_rule_engine_edge_cases():
    lines = [
        "wK . .",
        ". . .",
        ". . ."
    ]
    board = TextBoardParser().parse(lines)
    engine = RuleEngine()
    
    assert engine.outside_board(board, None, Cell(0, 0)) is True
    assert engine.outside_board(board, Cell(0, 0), None) is True
    assert engine.empty_source(board, None) is True
    assert engine.board_rules.friendly_destination(board, None, Cell(0, 0)) is False
    assert engine.board_rules.friendly_destination(board, Cell(0, 0), None) is False
    assert engine.is_piece_move_valid(board, None, Cell(0, 0)) is False
    assert engine.is_piece_move_valid(board, Cell(0, 0), None) is False
    
    cell_out = Cell(-1, 0)
    assert engine.empty_source(board, cell_out) is True
    assert engine.board_rules.friendly_destination(board, cell_out, Cell(0, 0)) is False
    assert engine.board_rules.friendly_destination(board, Cell(0, 0), cell_out) is False
    assert engine.is_piece_move_valid(board, cell_out, Cell(0, 0)) is False
    
    cell_empty = Cell(0, 1)
    assert engine.board_rules.friendly_destination(board, cell_empty, Cell(0, 0)) is False
    assert engine.is_piece_move_valid(board, cell_empty, Cell(0, 0)) is False
    
    bad_piece = Piece("w", "X", Cell(0, 0))
    board.grid[0][0] = bad_piece
    assert engine.is_piece_move_valid(board, Cell(0, 0), Cell(1, 1)) is False

def test_rule_engine_enemy_is_moving_allowed():
    lines = [
        "wK . .",
        ". . .",
        ". . bK"
    ]
    board = TextBoardParser().parse(lines)
    engine = RuleEngine()
    cell_from = Cell(0, 0)
    cell_to = Cell(1, 1)

    assert engine.is_move_valid(board, cell_from, cell_to, []) is True

    opp_piece = board.get_piece_at(Cell(2, 2))
    pending_moves = [PendingMove(Cell(2, 2), Cell(2, 1), opp_piece, 1000)]
    assert engine.is_move_valid(board, cell_from, cell_to, pending_moves) is True


def test_rule_engine_transit_validation():
    lines = [
        "wK . .",
        ". . .",
        ". . bK"
    ]
    board = TextBoardParser().parse(lines)
    engine = RuleEngine()
    
    cell_from = Cell(0, 0)
    cell_to = Cell(1, 1)
    
    moving_piece = board.get_piece_at(Cell(0, 0))
    from models.pieces import PieceStatus
    moving_piece.status = PieceStatus.MOVING
    pending_moves = [PendingMove(cell_from, cell_to, moving_piece, 1000)]
    
    assert engine.is_piece_moving(cell_from, board) is True
    assert engine.is_piece_moving(cell_to, board) is False
    assert engine.is_piece_moving(None, board) is False
    assert engine.is_piece_moving(cell_from, None) is False
    
    assert engine.board_rules.is_destination_reserved(cell_to, pending_moves) is True
    assert engine.board_rules.is_destination_reserved(cell_from, pending_moves) is False
    assert engine.board_rules.is_destination_reserved(None, pending_moves) is False
    assert engine.board_rules.is_destination_reserved(cell_to, None) is False
    
    assert engine.is_move_valid(board, cell_from, Cell(0, 1), pending_moves) is False
    
    other_piece = board.get_piece_at(Cell(2, 2))
    assert engine.is_move_valid(board, Cell(2, 2), cell_to, pending_moves) is False


def test_rule_engine_dependency_injection():
    from rules.board_rules import BoardRules
    
    class MockBoardRules(BoardRules):
        def is_move_valid(self, board, cell_from, cell_to, pending_moves=None):
            return True

    board = TextBoardParser().parse(["wK .", ". ."])
    mock_rules = MockBoardRules()
    engine = RuleEngine(board_rules=mock_rules)
    
    assert engine.is_move_valid(board, Cell(0, 0), Cell(0, 1)) is True

