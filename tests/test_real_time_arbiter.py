import pytest
from models.board import Board
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece
from models.pending_move import PendingMove
from models.jump import Jump
from realtime.real_time_arbiter import RealTimeArbiter

def test_real_time_arbiter_clock():
    board = Board(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    assert state.clock == 0
    arbiter.tick(state, 100)
    assert state.clock == 100
    arbiter.tick(state, 250)
    assert state.clock == 350

def test_real_time_arbiter_move_execution():
    board = Board(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    # White King moves from (0, 0) to (0, 1) arriving at t=200
    w_king = board.get_piece_at(0, 0)
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_king, 200))
    
    # Tick 100: clock becomes 100. Move shouldn't execute yet.
    arbiter.tick(state, 100)
    assert board.get_piece_at(0, 0) == w_king
    assert board.get_piece_at(0, 1) is None
    assert len(state.pending_moves) == 1
    
    # Tick 100 (clock becomes 200): move should execute
    arbiter.tick(state, 100)
    assert board.get_piece_at(0, 0) is None
    assert board.get_piece_at(0, 1) == w_king
    assert len(state.pending_moves) == 0

def test_real_time_arbiter_game_over_by_capture():
    board = Board(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_king = board.get_piece_at(0, 0)
    # White King captures Black King at (1, 1) arriving at t=100
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 1), w_king, 100))
    
    assert state.game_over is False
    arbiter.tick(state, 100) # Clock becomes 100, then executes the move and checks game over
    assert board.get_piece_at(1, 1) == w_king
    assert state.game_over is True

def test_real_time_arbiter_airborne_capture():
    board = Board(["wP .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_pawn = board.get_piece_at(0, 0)
    # White pawn moves to (0, 1) arriving at t=100
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_pawn, 100))
    
    # Black King jumps over/at (0, 1) from t=50 to t=150
    b_king = board.get_piece_at(1, 1)
    state.jumps.append(Jump((0, 1), 50, 150, b_king))
    
    arbiter.tick(state, 100) # Clock becomes 100, checks capture, executes
    # White pawn should be captured and removed (source cell cleared, target cell empty)
    assert board.get_piece_at(0, 0) is None
    assert board.get_piece_at(0, 1) is None
    assert len(state.pending_moves) == 0

def test_real_time_arbiter_source_changes():
    board = Board(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    # White King moves from (0, 0) to (0, 1) arriving at t=100
    w_king = board.get_piece_at(0, 0)
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_king, 100))
    
    # Simulate the piece's cell source changing (moved to (1, 0) instead in the meantime)
    w_king.cell = Cell(1, 0)
    board.grid[1][0] = w_king
    board.grid[0][0] = None
    
    arbiter.tick(state, 100)
    
    # It should clear from (1, 0) (actual current location) and place at (0, 1)
    assert board.grid[1][0] is None
    assert board.grid[0][1] == w_king
    assert w_king.cell == Cell(0, 1)

def test_real_time_arbiter_escaping_king():
    board = Board(["wR . bK", ". . ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_rook = board.get_piece_at(0, 0)
    b_king = board.get_piece_at(0, 2)
    
    # White Rook captures bK at (0, 2) arriving at t=100
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 2), w_rook, 100))
    
    # Black King escapes to (1, 2) arriving at t=150
    state.pending_moves.append(PendingMove(Cell(0, 2), Cell(1, 2), b_king, 150))
    
    arbiter.tick(state, 100)
    assert state.game_over is False
