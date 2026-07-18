import pytest
from models.board import Board
from services.board_parser import TextBoardParser
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece
from models.pending_move import PendingMove
from engine.game_engine import GameEngine
from services.jump_service import JumpService

def test_game_engine_schedule_move():
    board = TextBoardParser().parse([". .", "wP ."])
    state = GameState(board=board)
    engine = GameEngine()

    assert len(state.pending_moves) == 0
    engine.request_move(state, Cell(1, 0), Cell(0, 0))
    assert len(state.pending_moves) == 1
    
    move = state.pending_moves[0]
    assert move.from_pos == Cell(1, 0)
    assert move.to_pos == Cell(0, 0)
    assert move.piece == board.get_piece_at(Cell(1, 0))
    assert move.arrival == 1000

def test_game_engine_request_move_validation():
    # 1. game_over check
    board = TextBoardParser().parse(["wP .", ". ."])
    state = GameState(board=board)
    state.game_over = True
    engine = GameEngine()
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0

    # 2. game_engine.request_move edge cases
    state.game_over = False
    p = Piece.from_text("wP")
    # Outside bounds
    engine.request_move(state, Cell(0, 0), Cell(5, 5))
    assert len(state.pending_moves) == 0

    # Friendly destination
    board.grid[0][1] = Piece.from_text("wP")
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0
    board.grid[0][1] = None

    # Source is already moving
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 0), p, 1000))
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()

    # Destination is reserved
    state.pending_moves.append(PendingMove(Cell(1, 0), Cell(0, 1), p, 1000))
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()

    # Enemy is moving
    board.grid[0][1] = Piece.from_text("bP")
    state.pending_moves.append(PendingMove(Cell(0, 1), Cell(1, 1), Piece.from_text("bP"), 1000))
    engine.request_move(state, Cell(0, 0), Cell(1, 0))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()
    board.grid[0][1] = None

    # Source has a piece but the move is genuinely illegal
    engine.request_move(state, Cell(0, 0), Cell(1, 1))
    assert len(state.pending_moves) == 0

    # Knight distance calculation branch
    board_n = TextBoardParser().parse(["wN . .", ". . .", ". . ."])
    state_n = GameState(board=board_n)
    engine.request_move(state_n, Cell(0, 0), Cell(1, 2))
    assert len(state_n.pending_moves) == 1
    assert state_n.pending_moves[0].arrival == 3000

def test_jump_service():
    board = TextBoardParser().parse([". ."])
    state = GameState(board=board)
    service = JumpService()
    p_white = Piece.from_text("wP")

    service.schedule_jump(state, (2, 2), 100, p_white)
    assert len(state.jumps) == 1
    assert state.jumps[0].cell == (2, 2)

def test_game_engine_cooldown_movement():
    board = TextBoardParser().parse(["wR .", ". ."])
    state = GameState(board=board)
    engine = GameEngine()
    
    piece = board.get_piece_at(Cell(0, 0))
    # Put piece on cooldown
    piece.cooldown_until = 1000
    state.clock = 500
    
    # Try to move - should be ignored due to cooldown
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0
    
    # Advance clock past cooldown
    state.clock = 1000
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1

def test_game_engine_cooldown_jump():
    board = TextBoardParser().parse(["wR .", ". ."])
    state = GameState(board=board)
    engine = GameEngine()
    
    piece = board.get_piece_at(Cell(0, 0))
    # Put piece on cooldown
    piece.cooldown_until = 1000
    state.clock = 500
    
    assert engine.can_jump(state, Cell(0, 0)) is False
    
    # Advance clock past cooldown
    state.clock = 1000
    assert engine.can_jump(state, Cell(0, 0)) is True


def test_game_engine_dependency_injection():
    from rules.rule_engine import RuleEngine
    
    class MockRuleEngine(RuleEngine):
        def is_move_valid(self, board, from_cell, to_cell, pending_moves=None):
            return False

    board = TextBoardParser().parse(["wR .", ". ."])
    state = GameState(board=board)
    mock_rules = MockRuleEngine()
    engine = GameEngine(rule_engine=mock_rules)

    # Move rook - normally valid, but mock says invalid
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0

def test_game_engine_snapshot():
    board = TextBoardParser().parse(["wR .", ". ."])
    state = GameState(board=board)
    engine = GameEngine()
    snap = engine.snapshot(state)
    assert snap.clock == state.clock
    assert snap.game_over == state.game_over



