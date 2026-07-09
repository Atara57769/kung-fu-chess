import pytest
from typing import Tuple, List, Optional
from models.pieces import Piece, PieceFactory
get_piece = PieceFactory.get_piece
from models.board import Board
from services.jump_service import JumpService
from models.jump import Jump
from services.move_scheduler import MoveScheduler
from models.cell import Cell
from models.pending_move import PendingMove
from services.move_validation_service import MoveValidationService
from services.board_service import boardService
import io


# Mock piece for testing sub-service logic
class DummyPiece(Piece):
    def __init__(self, color: str, name_val: str = "P", is_king_val: bool = False, is_pawn_val: bool = False):
        kind = "K" if is_king_val else ("P" if is_pawn_val or name_val == "P" else "Q")
        if name_val == "R":
            kind = "R"
        elif name_val == "B":
            kind = "B"
        elif name_val == "N":
            kind = "N"
        super().__init__(color, kind)


def test_promotion():
    board = Board([". .", ". ."])
    scheduler = MoveScheduler(board, JumpService())
    
    # White pawn promoting at y=0 on 2x2 board
    p1 = Piece("w", "P", Cell(1, 0))
    move1 = PendingMove(Cell(1, 0), Cell(0, 0), p1, 1000)
    scheduler.execute_move(move1, is_captured=False)
    assert board.grid[0][0] == Piece("w", "Q", Cell(0, 0))
    
    # White pawn not promoting at y=1 on 2x2 board
    board.grid = [[None, None], [None, None]]
    p2 = Piece("w", "P", Cell(0, 0))
    move2 = PendingMove(Cell(0, 0), Cell(1, 0), p2, 1000)
    scheduler.execute_move(move2, is_captured=False)
    assert board.grid[1][0] == Piece("w", "P", Cell(1, 0))

    # Non-pawn (knight) not promoting
    board.grid = [[None, None], [None, None]]
    p3 = Piece("w", "N", Cell(1, 0))
    move3 = PendingMove(Cell(1, 0), Cell(0, 0), p3, 1000)
    scheduler.execute_move(move3, is_captured=False)
    assert board.grid[0][0] == Piece("w", "N", Cell(0, 0))


def get_token(val):
    if isinstance(val, Piece):
        return val.color + val.kind
    return val or "."

def test_game_over_service():
    board = Board(["wK bN", ". ."])
    
    def get_piece_mock(token: str) -> Optional[Piece]:
        if token == "wK":
            return DummyPiece("w", is_king_val=True)
        if token == "bN":
            return DummyPiece("b", is_king_val=False)
        return None

    board.get_piece_at = lambda y, x: get_piece_mock(get_token(board.grid[y][x]))
    scheduler = MoveScheduler(board, JumpService())
    
    assert scheduler.check_game_over(Cell(0, 0)) is True
    assert scheduler.check_game_over(Cell(0, 1)) is False
    assert scheduler.check_game_over(Cell(1, 0)) is False


def test_jump_service():
    service = JumpService()
    p_white = DummyPiece("w")
    p_black = DummyPiece("b")

    # Schedule a jump at (2, 2) from t=100 to t=1100
    service.schedule_jump((2, 2), 100, p_white)
    
    # Airborne capture checking:
    # 1. Target Cell match, inside time window, opposite color -> Captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_black) is True
    
    # 2. Same color -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_white) is False

    # 3. Target Cell match, outside time window -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 1200, p_black) is False

    # 4. Target Cell mismatch -> Not captured
    assert service.is_captured_by_airborne_enemy((1, 1), 500, p_black) is False


def test_move_scheduler():
    board = Board(["wP .", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    p = DummyPiece("w")
    
    scheduler.schedule_move(Cell(0, 0), Cell(1, 1), p, 1500)
    assert len(scheduler.get_pending_moves()) == 1
    assert scheduler.get_pending_moves()[0].arrival == 1500

    scheduler.advance_clock(500)
    assert scheduler.get_clock() == 500


def test_move_validation_service():
    board = Board(["wK .", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    service = MoveValidationService(board, scheduler)

    # is_within_bounds
    assert service.is_within_bounds(0, 0) is True
    assert service.is_within_bounds(-1, 0) is False
    assert service.is_within_bounds(0, 2) is False

    # is_piece_moving and is_destination_reserved
    p = DummyPiece("w")
    scheduler.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 1), p, 1000)]
    
    assert service.is_piece_moving(0, 0) is True
    assert service.is_piece_moving(1, 1) is False
    assert service.is_destination_reserved(0, 0) is False
    assert service.is_destination_reserved(1, 1) is True

    # is_legal_move
    assert service.is_legal_move(None, Cell(0, 0), Cell(1, 1)) is True
    assert service.is_legal_move(p, Cell(0, 0), Cell(1, 1)) is False  # wP/Dummy cannot move diagonally by rules module!


def test_move_execution_service():
    board = Board([". .", "wP ."])
    
    p_white_pawn = Piece("w", "P", Cell(1, 0))
    move = PendingMove(Cell(1, 0), Cell(0, 0), p_white_pawn, 1000)

    scheduler = MoveScheduler(board, JumpService())
    scheduler.check_game_over = lambda target_cell: True

    # Move success, check promotion and game over propagation
    is_game_over = scheduler.execute_move(move, is_captured=False)
    assert is_game_over is True
    assert board.grid[1][0] is None
    assert board.grid[0][0] == Piece("w", "Q", Cell(0, 0))

    # Reset and test captured in transit case
    board2 = Board([". .", "wP ."])
    scheduler2 = MoveScheduler(board2, JumpService())
    scheduler2.check_game_over = lambda target_cell: True
    is_game_over_captured = scheduler2.execute_move(move, is_captured=True)
    assert is_game_over_captured is False
    assert board2.grid[1][0] is None
    assert board2.grid[0][0] is None


def test_board_service_di():
    # Verify that boardService can construct and run cleanly with custom dependency injection
    board = Board(["wP .", ". ."])
    
    custom_jump = JumpService()
    custom_scheduler = MoveScheduler(board, custom_jump)
    custom_validation = MoveValidationService(board, custom_scheduler)

    import sys
    service = boardService(
        board=board,
        stdout=sys.stdout,
        move_scheduler=custom_scheduler,
        move_validation_service=custom_validation,
        jump_service=custom_jump,
    )

    # Check dependencies are injected correctly
    assert service.move_scheduler is custom_scheduler
    assert service.move_validation_service is custom_validation
    assert service.jump_service is custom_jump

    # Test basic integration
    service.click(0, 0) # Select wP at (0, 0)
    assert service.selected_piece == (0, 0)

    # Verify clock and pending_moves properties redirect successfully
    assert service.move_scheduler.get_clock() == 0
    service.move_scheduler.clock = 100
    assert custom_scheduler.get_clock() == 100

    assert len(service.move_scheduler.get_pending_moves()) == 0
    p = DummyPiece("w")
    service.move_scheduler.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 1), p, 200)]
    assert len(custom_scheduler.get_pending_moves()) == 1

    assert len(service.jump_service.jumps) == 0
    service.jump_service.jumps = [Jump((0, 0), 0, 100, p)]
    assert len(custom_jump.jumps) == 1


def test_move_validation_service_direct():
    board = Board(["wK wP", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    service = MoveValidationService(board, scheduler)

    # 1. Target out of bounds
    is_val = service.validate_move(0, 0, 5, 5)
    assert is_val is False

    # 2. Friendly target
    is_val = service.validate_move(0, 0, 0, 1)
    assert is_val is False

    # 3. Illegal move
    class IllegalPiece(Piece):
        def __init__(self, color):
            super().__init__(color, "X")

    board.grid[0][0] = "wX"
    def get_illegal_piece(token):
        if token == "wX": return IllegalPiece("w")
        return get_piece(token)

    board.get_piece_at = lambda y, x: get_illegal_piece(get_token(board.grid[y][x]))
    is_val = service.validate_move(0, 0, 1, 1)
    assert is_val is False


def test_board_service_game_over_triggers():
    import sys
    board = Board(["wP bK", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    validation = MoveValidationService(board, scheduler)
    
    p_pawn = get_piece("wP")
    scheduler.schedule_move(Cell(0, 0), Cell(0, 1), p_pawn, 1000)
    
    # 1. wait() causes game over
    service = boardService(board, sys.stdout, scheduler, validation, jump_service)
    service.wait(1000)
    assert service.game_over is True

    # Reset and check print_board() does not trigger game over, but wait() does
    board2 = Board(["wP bK", ". ."])
    scheduler2 = MoveScheduler(board2, jump_service)
    validation2 = MoveValidationService(board2, scheduler2)
    scheduler2.schedule_move(Cell(0, 0), Cell(0, 1), p_pawn, 1000)
    scheduler2.advance_clock(1000)
    service2 = boardService(board2, io.StringIO(), scheduler2, validation2, jump_service)
    service2.print_board()
    assert service2.game_over is False
    service2.wait(0)
    assert service2.game_over is True

    # Reset and check jump() does not trigger game over, but wait() does
    board3 = Board(["wP bK", ". ."])
    scheduler3 = MoveScheduler(board3, jump_service)
    validation3 = MoveValidationService(board3, scheduler3)
    scheduler3.schedule_move(Cell(0, 0), Cell(0, 1), p_pawn, 1000)
    scheduler3.advance_clock(1000)
    service3 = boardService(board3, sys.stdout, scheduler3, validation3, jump_service)
    service3.jump(0, 0)
    assert service3.game_over is False
    service3.wait(0)
    assert service3.game_over is True


def test_board_service_click_game_over():
    import sys
    board = Board(["wP bK", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    validation = MoveValidationService(board, scheduler)
    
    p_pawn = get_piece("wP")
    scheduler.schedule_move(Cell(0, 0), Cell(0, 1), p_pawn, 1000)
    scheduler.advance_clock(1000)
    
    service = boardService(board, sys.stdout, scheduler, validation, jump_service)
    service.click(50, 0)
    assert service.game_over is False
    service.wait(0)
    assert service.game_over is True

    service.click(50, 0)
    assert service.game_over is True
