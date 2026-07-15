from models.cell import Cell
from models.pieces import Piece, PieceStatus
from models.game_state import GameState
from models.board import Board
from services.move_scheduler import MoveScheduler
from realtime.real_time_arbiter import RealTimeArbiter

def test_piece_status_lifecycle():
    # 1. Test default status
    piece = Piece("w", "P", Cell(0, 0))
    assert piece.status == PieceStatus.IDLE

    # 2. Test status becomes MOVING when scheduled
    board = Board([[piece, None]], 2, 1)
    state = GameState(board=board)
    scheduler = MoveScheduler()
    move = scheduler.create_pending_move(Cell(0, 0), Cell(0, 1), piece, 1000)
    
    # Not moving yet (just created, not added to pending)
    assert piece.status == PieceStatus.IDLE
    
    scheduler.add_to_pending(state, move)
    # Now it should be MOVING
    assert piece.status == PieceStatus.MOVING

    # 3. Test status becomes IDLE when resolved via RealTimeArbiter
    arbiter = RealTimeArbiter()
    arbiter.tick(state, 1000) # advances clock to 1000 and resolves the move
    assert piece.status == PieceStatus.IDLE
