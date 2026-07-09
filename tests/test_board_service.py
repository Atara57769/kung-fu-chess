import pytest
import io
import sys
from dataclasses import dataclass
from typing import Tuple, List, Optional
from models.board import Board
from models.pieces import Piece, get_piece
from services.board_service import boardService
from services.jump_service import JumpService
from models.jump import Jump
from services.move_scheduler import MoveScheduler
from models.cell import Cell
from models.pending_move import PendingMove
from services.move_validation_service import MoveValidationService


# Simple mock Piece for testing DI and behavior
class MockSimplePiece(Piece):
    def __init__(self, color, name_val="P", is_king_val=False, is_pawn_val=False):
        super().__init__(color)
        self._name = name_val
        self._is_king = is_king_val
        self._is_pawn = is_pawn_val

    @property
    def is_king(self) -> bool:
        return self._is_king

    @property
    def is_pawn(self) -> bool:
        return self._is_pawn

    @property
    def name(self) -> str:
        return self._name

    def is_legal_move(self, board, from_pos: Cell, to_pos: Cell) -> bool:
        # Allow all moves for mock tests unless it's a specific Cell
        if to_pos.y == 9 and to_pos.x == 9:
            return False
        return True

    def promote(self, to_y: int, grid_height: int) -> str:
        if self._is_pawn:
            is_white_promotion = (self.color == 'w' and to_y == 0)
            is_black_promotion = (self.color == 'b' and to_y == grid_height - 1)
            if is_white_promotion or is_black_promotion:
                return self.color + "Q"
        return self.token


def create_service(board, get_piece_fn=get_piece, stdout=sys.stdout):
    if get_piece_fn is not get_piece:
        board.get_piece_at = lambda y, x: get_piece_fn(board.grid[y][x])
    jump_service = JumpService()
    scheduler = MoveScheduler(board, jump_service)
    validation = MoveValidationService(board, scheduler)

    return boardService(
        board=board,
        stdout=stdout,
        move_scheduler=scheduler,
        move_validation_service=validation,
        jump_service=jump_service,
    )


def test_board_service_bounds():
    board = Board(["wK .", ". ."])
    service = create_service(board)
    assert service.move_validation_service.is_within_bounds(0, 0) is True
    assert service.move_validation_service.is_within_bounds(1, 1) is True
    assert service.move_validation_service.is_within_bounds(-1, 0) is False
    assert service.move_validation_service.is_within_bounds(0, 2) is False
    assert service.move_validation_service.is_within_bounds(2, 0) is False


def test_board_service_movement_queries():
    board = Board(["wK .", ". ."])
    service = create_service(board)
    p = MockSimplePiece("w")
    service.move_scheduler.get_pending_moves().append(PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=p,
        arrival=1000
    ))
    assert service.move_validation_service.is_piece_moving(0, 0) is True
    assert service.move_validation_service.is_piece_moving(1, 1) is False
    assert service.move_validation_service.is_destination_reserved(0, 0) is False
    assert service.move_validation_service.is_destination_reserved(1, 1) is True


def test_board_service_airborne_enemy_capture():
    board = Board(["wP .", ". bP"])
    service = create_service(board)
    
    white_piece = MockSimplePiece("w")
    black_piece = MockSimplePiece("b")
    
    # Add a jump by white piece on cell (1, 1) from t=0 to t=1000
    service.jump_service.jumps.append(Jump(
        cell=(1, 1),
        start=0,
        end=1000,
        piece=white_piece
    ))
    
    # Black piece arrives at (1, 1) at t=500. Should be captured by white airborne enemy.
    assert service.jump_service.is_captured_by_airborne_enemy((1, 1), 500, black_piece) is True
    
    # White piece arrives at (1, 1) at t=500. Same color, should NOT be captured.
    assert service.jump_service.is_captured_by_airborne_enemy((1, 1), 500, white_piece) is False
    
    # Black piece arrives at (1, 1) at t=1500 (after jump ended).
    assert service.jump_service.is_captured_by_airborne_enemy((1, 1), 1500, black_piece) is False
    
    # Black piece arrives at (0, 0) (different cell).
    assert service.jump_service.is_captured_by_airborne_enemy((0, 0), 500, black_piece) is False


def test_board_service_check_game_over():
    board = Board(["wK bK", ". ."])
    
    def get_piece_mock(token):
        if token == "wK":
            return MockSimplePiece("w", is_king_val=True)
        if token == "bK":
            return MockSimplePiece("b", is_king_val=True)
        return None

    board.get_piece_at = lambda y, x: get_piece_mock(board.grid[y][x])
    scheduler = MoveScheduler(board, JumpService())
    # destination has non-king (empty)
    assert scheduler.check_game_over(Cell(1, 0)) is False

    # destination has king
    assert scheduler.check_game_over(Cell(0, 1)) is True


def test_execute_move_captured():
    board = Board(["wP .", ". ."])
    scheduler = MoveScheduler(board, JumpService())
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=MockSimplePiece("w"),
        arrival=1000
    )
    # Piece is captured. Grid at from_pos should be cleared.
    scheduler.execute_move(move, is_captured=True)
    assert board.grid[0][0] == "."
    assert board.grid[1][1] == "."

    # Check that source is not cleared if the token doesn't match
    board2 = Board(["wP .", ". ."])
    scheduler2 = MoveScheduler(board2, JumpService())
    # Alter source token first
    board2.grid[0][0] = "."
    scheduler2.execute_move(move, is_captured=True)
    assert board2.grid[0][0] == "."


def test_execute_move_success():
    board = Board(["wP .", ". ."])
    scheduler = MoveScheduler(board, JumpService())
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=MockSimplePiece("w"),
        arrival=1000
    )
    scheduler.execute_move(move, is_captured=False)
    assert board.grid[0][0] == "."
    assert board.grid[1][1] == "wP"

    # With non-matching source token
    board2 = Board(["wP .", ". ."])
    scheduler2 = MoveScheduler(board2, JumpService())
    board2.grid[0][0] = "bK"
    move2 = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=MockSimplePiece("w"),
        arrival=1000
    )
    scheduler2.execute_move(move2, is_captured=False)
    assert board2.grid[0][0] == "bK"
    assert board2.grid[1][1] == "wP"


def test_apply_completed_moves():
    board = Board(["wP .", ". ."])
    service = create_service(board)
    p = MockSimplePiece("w")
    service.move_scheduler.get_pending_moves().extend([
        PendingMove(Cell(0, 0), Cell(1, 1), p, 1000),
        PendingMove(Cell(0, 1), Cell(1, 0), p, 2000)
    ])
    
    # Wait until t=500. Nothing should happen.
    service.wait(500)
    assert len(service.move_scheduler.get_pending_moves()) == 2
    
    # Wait until t=1200. First move should execute.
    service.wait(700) # clock is now 1200
    assert len(service.move_scheduler.get_pending_moves()) == 1
    assert board.grid[1][1] == "wP"
    assert board.grid[0][0] == "."


def test_click_edge_cases():
    board = Board(["wP .", ". bP"])
    service = create_service(board)

    # Click out of bounds
    service.click(-100, 0)
    assert service.selected_piece is None

    # Click empty cell when nothing selected
    service.click(150, 0) # cell (0, 1) -> '.'
    assert service.selected_piece is None

    # Click non-empty cell -> selects it
    service.click(50, 0) # cell (0, 0) -> 'wP'
    assert service.selected_piece == (0, 0)

    # Click a friendly piece when another friendly is selected -> change selection
    board_friendly = Board(["wP wP", ". ."])
    service_friendly = create_service(board_friendly)
    service_friendly.click(50, 0) # selects (0, 0)
    assert service_friendly.selected_piece == (0, 0)
    service_friendly.click(150, 0) # clicks (0, 1) -> friendly wP
    assert service_friendly.selected_piece == (0, 1) # selection updated!


def test_click_move_scheduling():
    # Use a board layout where white pawn (wP) at (1, 0) can legally move to (0, 0).
    board = Board([". .", "wP ."])
    service = create_service(board)

    # Click and select (1, 0)
    service.click(50, 100)
    assert service.selected_piece == (1, 0)
    # Click (0, 0) -> schedules move
    service.click(50, 0)
    assert len(service.move_scheduler.get_pending_moves()) == 1
    assert service.selected_piece is None
    assert service.move_scheduler.get_pending_moves()[0].from_pos == Cell(1, 0)
    assert service.move_scheduler.get_pending_moves()[0].to_pos == Cell(0, 0)


def test_click_move_scheduling_none_piece():
    board = Board([". .", "wP ."])
    service = create_service(board)
    # Click and select (1, 0)
    service.click(50, 100)
    assert service.selected_piece == (1, 0)
    # Clear the board grid at that spot, so piece resolves to None
    board.grid[1][0] = "."
    # Click (0, 0) -> schedules move with None piece and default duration 1000
    service.click(50, 0)
    assert len(service.move_scheduler.get_pending_moves()) == 1
    assert service.move_scheduler.get_pending_moves()[0].piece is None
    assert service.move_scheduler.get_pending_moves()[0].arrival == 1000


def test_click_while_moving_or_reserved_tricked():
    class TrickList(list):
        def __bool__(self):
            return False

    board = Board(["wP wP", ". ."])
    service = create_service(board)
    service.move_scheduler.apply_completed_moves = lambda: False
    
    # 1. Test clicking a cell that is currently moving (first check: cell_y, cell_x is moving)
    p = get_piece("wP")
    service.move_scheduler.pending_moves = TrickList([PendingMove(Cell(0, 0), Cell(1, 0), p, 1000)])
    service.click(50, 0) # Click (0, 0) which is moving
    assert service.selected_piece is None

    # 2. Test selected piece is already in transit (third check: sel_y, sel_x is moving)
    service.selected_piece = (0, 0)
    service.click(50, 100) # Clicks (1, 0)
    assert len(service.move_scheduler.get_pending_moves()) == 1
    assert service.selected_piece == (0, 0)

    # 3. Test destination is targeted by another pending move (fourth check: destination reserved)
    service.move_scheduler.pending_moves = TrickList([PendingMove(Cell(0, 1), Cell(1, 0), p, 1000)])
    service.selected_piece = (0, 0) # (0, 0) is not moving
    service.click(50, 100) # Click (1, 0) (destination is reserved)
    assert len(service.move_scheduler.get_pending_moves()) == 1
    assert service.selected_piece == (0, 0)


def test_click_game_over_and_pending_moves_return():
    board = Board(["wP .", ". ."])
    service = create_service(board)
    service.game_over = True
    service.click(50, 0)
    assert service.selected_piece is None

    service.game_over = False
    service.move_scheduler.get_pending_moves().append(PendingMove(Cell(0, 0), Cell(1, 1), MockSimplePiece("w"), 1000))
    service.click(50, 0)
    assert service.selected_piece is None


def test_click_illegal_move_retains_selection():
    # Use DI to provide a piece that returns False for is_legal_move
    board = Board(["wP .", ". ."])
    mock_piece = MockSimplePiece("w")
    def mock_get_piece(token):
        if token == "wP":
            return mock_piece
        return None

    service = create_service(board, get_piece_fn=mock_get_piece)
    # Select (0, 0)
    service.click(50, 0)
    assert service.selected_piece == (0, 0)
    # Move to illegal target Cells
    service.click(950, 950)
    # Selection should still be retained
    assert service.selected_piece == (0, 0)
    assert len(service.move_scheduler.get_pending_moves()) == 0


def test_jump():
    board = Board(["wP .", ". ."])
    service = create_service(board)

    # Jump out of bounds
    service.jump(-100, 0)
    assert len(service.jump_service.jumps) == 0

    # Jump on empty cell
    service.jump(150, 0) # cell (0, 1) -> '.'
    assert len(service.jump_service.jumps) == 0

    # Jump on moving piece (ignored)
    p = get_piece("wP")
    service.move_scheduler.get_pending_moves().append(PendingMove(Cell(0, 0), Cell(1, 0), p, 1000))
    service.jump(50, 0) # cell (0, 0)
    assert len(service.jump_service.jumps) == 0

    # Jump on destination reserved cell (ignored)
    service.jump(50, 100) # cell (1, 0) -> reserved destination
    assert len(service.jump_service.jumps) == 0

    # Valid jump
    service.move_scheduler.get_pending_moves().clear()
    service.jump(50, 0)
    assert len(service.jump_service.jumps) == 1
    assert service.jump_service.jumps[0].cell == (0, 0)
    assert service.jump_service.jumps[0].start == 0
    assert service.jump_service.jumps[0].end == 1000

    # Jump after game over (ignored)
    service.game_over = True
    service.jump_service.jumps.clear()
    service.jump(50, 0)
    assert len(service.jump_service.jumps) == 0


def test_print_board():
    board = Board(["wP .", ". bP"])
    output = io.StringIO()
    service = create_service(board, stdout=output)
    service.print_board()
    assert output.getvalue() == "wP .\n. bP\n"
