from models.cell import Cell
from models.pending_move import PendingMove
from models.pieces import Piece
from models.game_state import GameState
from models.board import Board
from services.collision_service import CollisionService
from models.piece_type import PieceType

def test_moves_dont_meet_parallel():
    service = CollisionService()
    
    # Two pieces moving in parallel at the same time
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(0, 1))
    
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000)
    m2 = PendingMove(Cell(0, 1), Cell(2, 1), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is False

def test_moves_meet_opposite():
    service = CollisionService()
    
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    # Meet at t = 1000 in the middle
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000)
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is True

def test_moves_meet_opposite_horizontal():
    service = CollisionService()
    
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(0, 2))
    
    # Meet at t = 1000 in the middle (horizontal)
    m1 = PendingMove(Cell(0, 0), Cell(0, 2), p1, 2000)
    m2 = PendingMove(Cell(0, 2), Cell(0, 0), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is True

def test_moves_meet_offset_time():
    service = CollisionService()
    
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    # Offset start: m1 starts at 0, m2 starts at 1000
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000)
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 3000)
    
    assert service.moves_meet_in_middle(m1, m2) is True

def test_knight_ignored_in_collision():
    service = CollisionService()
    
    p1 = Piece("w", PieceType.KNIGHT, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    m1 = PendingMove(Cell(0, 0), Cell(2, 1), p1, 3000)
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    # Even if trajectories overlap in space/time, Knight is ignored
    assert service.moves_meet_in_middle(m1, m2) is False

def test_check_mid_move_collision():
    service = CollisionService()
    
    board = Board([[None]*3 for _ in range(3)], 3, 3)
    state = GameState(board=board)
    
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    # m1 is already in pending_moves
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000)
    state.pending_moves.append(m1)
    
    # m2 is the new move being scheduled
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    assert service.check_mid_move_collision(state, m2) is True

def test_zero_duration():
    service = CollisionService()
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    m1 = PendingMove(Cell(0, 0), Cell(0, 0), p1, 2000)
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is False

def test_no_time_overlap():
    service = CollisionService()
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    
    # m1 starts at 1000, ends at 2000
    m1 = PendingMove(Cell(0, 0), Cell(1, 0), p1, 2000)
    # m2 starts at 4000, ends at 5000
    m2 = PendingMove(Cell(2, 0), Cell(1, 0), p2, 5000)
    
    assert service.moves_meet_in_middle(m1, m2) is False

def test_moves_meet_diagonal_crossing():
    service = CollisionService()
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(1, 2))
    
    # Trajectories that cross in space and time diagonally
    m1 = PendingMove(Cell(0, 0), Cell(2, 2), p1, 2000)
    m2 = PendingMove(Cell(1, 2), Cell(1, 0), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is True

def test_moves_meet_completely_overlapping():
    service = CollisionService()
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    p2 = Piece("b", PieceType.ROOK, Cell(0, 0))
    
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000)
    m2 = PendingMove(Cell(0, 0), Cell(2, 0), p2, 2000)
    
    assert service.moves_meet_in_middle(m1, m2) is True

def test_check_mid_move_collision_with_invalid_pieces():
    service = CollisionService()
    board = Board([[None]*3 for _ in range(3)], 3, 3)
    state = GameState(board=board)
    
    # existing move with piece = None
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), None, 2000)
    state.pending_moves.append(m1)
    
    # existing move with Knight piece
    p_knight = Piece("w", PieceType.KNIGHT, Cell(0, 1))
    m_knight = PendingMove(Cell(0, 1), Cell(2, 2), p_knight, 3000)
    state.pending_moves.append(m_knight)
    
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    assert service.check_mid_move_collision(state, m2) is False

def test_check_mid_move_collision_with_already_captured():
    service = CollisionService()
    board = Board([[None]*3 for _ in range(3)], 3, 3)
    state = GameState(board=board)
    
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    m1 = PendingMove(Cell(0, 0), Cell(2, 0), p1, 2000, is_captured=True)
    state.pending_moves.append(m1)
    
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    m2 = PendingMove(Cell(2, 0), Cell(0, 0), p2, 2000)
    
    assert service.check_mid_move_collision(state, m2) is False

def test_game_engine_schedule_move_sets_captured():
    from engine.game_engine import GameEngine
    board = Board([[None]*3 for _ in range(3)], 3, 3)
    state = GameState(board=board)
    
    engine = GameEngine()
    
    # First move
    p1 = Piece("w", PieceType.ROOK, Cell(0, 0))
    board.grid[0][0] = p1
    engine.request_move(state, Cell(0, 0), Cell(2, 0))
    
    # Second move (starts at 2,0 and collides)
    p2 = Piece("b", PieceType.ROOK, Cell(2, 0))
    board.grid[2][0] = p2
    engine.request_move(state, Cell(2, 0), Cell(0, 0))
    
    assert state.pending_moves[1].is_captured is True
