import pytest
from typing import Tuple, List, Optional
from models.pieces import Piece, Queen, King, Pawn, get_piece
from models.board import Board
from services.jump_service import JumpService
from models.jump import Jump
from services.move_scheduler import MoveScheduler
from models.coordinate import Coordinate
from models.pending_move import PendingMove
from services.move_validation_service import MoveValidationService
from services.board_service import boardService
import io


# Mock piece for testing sub-service logic
class DummyPiece(Piece):
    def __init__(self, color: str, name_val: str = "P", is_king_val: bool = False, is_pawn_val: bool = False):
        super().__init__(color)
        self._name = name_val
        self._is_king = is_king_val
        self._is_pawn = is_pawn_val

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_king(self) -> bool:
        return self._is_king

    @property
    def is_pawn(self) -> bool:
        return self._is_pawn

    def is_legal_move(self, board, from_pos: Coordinate, to_pos: Coordinate) -> bool:
        return True


def test_promotion():
    # White pawn promoting
    p_white_pawn = Pawn("w")
    assert p_white_pawn.promote(0, 8) == "wQ"
    # White pawn not promoting
    assert p_white_pawn.promote(1, 8) == "wP"

    # Black pawn promoting
    p_black_pawn = Pawn("b")
    assert p_black_pawn.promote(7, 8) == "bQ"
    # Black pawn not promoting
    assert p_black_pawn.promote(6, 8) == "bP"

    # Non-pawn (base class promote)
    from models.pieces import Knight
    p_knight = Knight("w")
    assert p_knight.promote(0, 8) == "wN"


def test_game_over_service():
    board = Board(["wK bN", ". ."])
    
    def get_piece_mock(token: str) -> Optional[Piece]:
        if token == "wK":
            return DummyPiece("w", is_king_val=True)
        if token == "bN":
            return DummyPiece("b", is_king_val=False)
        return None

    board.get_piece_at = lambda y, x: get_piece_mock(board.grid[y][x])
    scheduler = MoveScheduler(board, JumpService())
    
    assert scheduler.check_game_over(Coordinate(0, 0)) is True
    assert scheduler.check_game_over(Coordinate(0, 1)) is False
    assert scheduler.check_game_over(Coordinate(1, 0)) is False


def test_jump_service():
    service = JumpService()
    p_white = DummyPiece("w")
    p_black = DummyPiece("b")

    # Schedule a jump at (2, 2) from t=100 to t=1100
    service.schedule_jump((2, 2), 100, p_white)
    
    # Airborne capture checking:
    # 1. Target coordinate match, inside time window, opposite color -> Captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_black) is True
    
    # 2. Same color -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_white) is False

    # 3. Target coordinate match, outside time window -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 1200, p_black) is False

    # 4. Target coordinate mismatch -> Not captured
    assert service.is_captured_by_airborne_enemy((1, 1), 500, p_black) is False


def test_move_scheduler():
    board = Board(["wP .", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    p = DummyPiece("w")
    
    scheduler.schedule_move(Coordinate(0, 0), Coordinate(1, 1), p, 1500)
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
    scheduler.pending_moves = [PendingMove(Coordinate(0, 0), Coordinate(1, 1), p, 1000)]
    
    assert service.is_piece_moving(0, 0) is True
    assert service.is_piece_moving(1, 1) is False
    assert service.is_destination_reserved(0, 0) is False
    assert service.is_destination_reserved(1, 1) is True

    # is_legal_move
    assert service.is_legal_move(None, Coordinate(0, 0), Coordinate(1, 1)) is True
    assert service.is_legal_move(p, Coordinate(0, 0), Coordinate(1, 1)) is True


def test_move_execution_service():
    board = Board(["wP .", ". ."])
    
    class PromotableDummyPiece(DummyPiece):
        def promote(self, to_y, grid_height):
            return "wQ"

    p_white_pawn = PromotableDummyPiece("w", name_val="P", is_pawn_val=True)
    move = PendingMove(Coordinate(0, 0), Coordinate(1, 1), p_white_pawn, 1000)

    scheduler = MoveScheduler(board, JumpService())
    scheduler.check_game_over = lambda target_cell: True

    # Move success, check promotion and game over propagation
    is_game_over = scheduler.execute_move(move, is_captured=False)
    assert is_game_over is True
    assert board.grid[0][0] == "."
    assert board.grid[1][1] == "wQ"

    # Reset and test captured in transit case
    board2 = Board(["wP .", ". ."])
    scheduler2 = MoveScheduler(board2, JumpService())
    scheduler2.check_game_over = lambda target_cell: True
    is_game_over_captured = scheduler2.execute_move(move, is_captured=True)
    assert is_game_over_captured is False
    assert board2.grid[0][0] == "."
    assert board2.grid[1][1] == "."


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
    service.move_scheduler.pending_moves = [PendingMove(Coordinate(0, 0), Coordinate(1, 1), p, 200)]
    assert len(custom_scheduler.get_pending_moves()) == 1

    assert len(service.jump_service.jumps) == 0
    service.jump_service.jumps = [Jump((0, 0), 0, 100, p)]
    assert len(custom_jump.jumps) == 1

    # Cover piece promote customization
    class CustomPromotePiece(DummyPiece):
        def promote(self, to_y, grid_height):
            return "custom_promo"
    
    custom_p = CustomPromotePiece("w")
    assert custom_p.promote(0, 8) == "custom_promo"


def test_move_validation_service_direct():
    board = Board(["wK wP", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    service = MoveValidationService(board, scheduler)

    # 1. Target out of bounds
    is_val, piece, duration = service.validate_move(0, 0, 5, 5)
    assert is_val is False

    # 2. Friendly target
    is_val, piece, duration = service.validate_move(0, 0, 0, 1)
    assert is_val is False

    # 3. Illegal move
    class IllegalPiece(Piece):
        @property
        def name(self): return "P"
        def is_legal_move(self, board, from_pos, to_pos): return False

    board.grid[0][0] = "wX"
    def get_illegal_piece(token):
        if token == "wX": return IllegalPiece("w")
        return get_piece(token)

    board.get_piece_at = lambda y, x: get_illegal_piece(board.grid[y][x])
    is_val, piece, duration = service.validate_move(0, 0, 1, 1)
    assert is_val is False


def test_board_service_game_over_triggers():
    import sys
    board = Board(["wP bK", ". ."])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    validation = MoveValidationService(board, scheduler)
    
    p_pawn = get_piece("wP")
    scheduler.schedule_move(Coordinate(0, 0), Coordinate(0, 1), p_pawn, 1000)
    
    # 1. wait() causes game over
    service = boardService(board, sys.stdout, scheduler, validation, jump_service)
    service.wait(1000)
    assert service.game_over is True

    # Reset and check print_board() does not trigger game over, but wait() does
    board2 = Board(["wP bK", ". ."])
    scheduler2 = MoveScheduler(board2, jump_service)
    validation2 = MoveValidationService(board2, scheduler2)
    scheduler2.schedule_move(Coordinate(0, 0), Coordinate(0, 1), p_pawn, 1000)
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
    scheduler3.schedule_move(Coordinate(0, 0), Coordinate(0, 1), p_pawn, 1000)
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
    scheduler.schedule_move(Coordinate(0, 0), Coordinate(0, 1), p_pawn, 1000)
    scheduler.advance_clock(1000)
    
    service = boardService(board, sys.stdout, scheduler, validation, jump_service)
    service.click(50, 0)
    assert service.game_over is False
    service.wait(0)
    assert service.game_over is True

    service.click(50, 0)
    assert service.game_over is True
