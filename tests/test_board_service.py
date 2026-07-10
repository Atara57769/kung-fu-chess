import pytest
import io
import sys
from dataclasses import dataclass
from typing import Tuple, List, Optional
from models.board import Board
from models.pieces import Piece, PieceFactory
get_piece = PieceFactory.get_piece
from services.jump_service import JumpService
from models.jump import Jump
from models.cell import Cell
from models.pending_move import PendingMove
from models.game_state import GameState
from engine.controller import Controller
from engine.game_engine import GameEngine
from rules.rule_engine import RuleEngine


# Simple mock Piece for testing DI and behavior
class MockSimplePiece(Piece):
    def __init__(self, color, name_val="P", is_king_val=False, is_pawn_val=False):
        kind = "K" if is_king_val else ("P" if is_pawn_val or name_val == "P" else "Q")
        if name_val == "R":
            kind = "R"
        elif name_val == "B":
            kind = "B"
        elif name_val == "N":
            kind = "N"
        super().__init__(color, kind)


def get_token(val):
    if isinstance(val, Piece):
        return val.color + val.kind
    return val or "."

def check_cell(board, y, x, expected):
    val = board.grid[y][x]
    if expected == "." or expected is None:
        assert val is None or val == "."
    else:
        if isinstance(val, Piece):
            assert val.color + val.kind == expected
        else:
            assert val == expected

def create_state(board):
    return GameState(board=board)

def create_controller(board, stdout=sys.stdout):
    state = create_state(board)
    engine = GameEngine()
    return Controller(state, engine, stdout), state

def create_controller_with_state(state, stdout=sys.stdout):
    engine = GameEngine()
    return Controller(state, engine, stdout)


def test_controller_bounds():
    """Tests that is_within_bounds works via RuleEngine (used internally)."""
    board = Board(["wK .", ". ."])
    rule = RuleEngine()
    # Use the board's bounds (2x2)
    assert board.is_inside_bounds(0, 0) is True
    assert board.is_inside_bounds(1, 1) is True
    assert board.is_inside_bounds(-1, 0) is False
    assert board.is_inside_bounds(0, 2) is False
    assert board.is_inside_bounds(2, 0) is False


def test_controller_movement_queries():
    board = Board(["wK .", ". ."])
    state = create_state(board)
    p = MockSimplePiece("w")
    state.pending_moves.append(PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=p,
        arrival=1000
    ))
    rule = RuleEngine()
    assert rule.is_piece_moving(Cell(0, 0), state.pending_moves) is True
    assert rule.is_piece_moving(Cell(1, 1), state.pending_moves) is False
    assert rule.is_destination_reserved(Cell(0, 0), state.pending_moves) is False
    assert rule.is_destination_reserved(Cell(1, 1), state.pending_moves) is True



def test_controller_check_game_over():
    board = Board(["wK bK", ". ."])

    def get_piece_mock(token):
        if token == "wK":
            return MockSimplePiece("w", is_king_val=True)
        if token == "bK":
            return MockSimplePiece("b", is_king_val=True)
        return None

    board.get_piece_at = lambda y, x: get_piece_mock(get_token(board.grid[y][x]))
    from realtime.real_time_arbiter import RealTimeArbiter
    state = create_state(board)
    arbiter = RealTimeArbiter()
    # destination has non-king (empty)
    assert arbiter.check_game_over(state, Cell(1, 0)) is False

    # destination has king
    assert arbiter.check_game_over(state, Cell(0, 1)) is True


def test_execute_move_captured():
    from realtime.real_time_arbiter import RealTimeArbiter
    board = Board(["wP .", ". ."])
    state = create_state(board)
    arbiter = RealTimeArbiter()
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=MockSimplePiece("w"),
        arrival=1000
    )
    # Piece is captured. Grid at from_pos should be cleared.
    arbiter.execute_capture(state, move)
    check_cell(board, 0, 0, ".")

    # Check that source is not cleared if the token doesn't match
    board2 = Board(["wP .", ". ."])
    state2 = create_state(board2)
    board2.grid[0][0] = None
    arbiter.execute_capture(state2, move)
    check_cell(board2, 0, 0, ".")


def test_execute_move_success():
    from realtime.real_time_arbiter import RealTimeArbiter
    board = Board(["wP .", ". ."])
    state = create_state(board)
    arbiter = RealTimeArbiter()
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=MockSimplePiece("w"),
        arrival=1000
    )
    arbiter.execute_move_on_board(state, move)
    check_cell(board, 0, 0, ".")
    check_cell(board, 1, 1, "wP")


def test_apply_completed_moves():
    board = Board(["wP .", ". ."])
    controller, state = create_controller(board)
    p = MockSimplePiece("w")
    state.pending_moves.extend([
        PendingMove(Cell(0, 0), Cell(1, 1), p, 1000),
        PendingMove(Cell(0, 1), Cell(1, 0), p, 2000)
    ])

    # Wait until t=500. Nothing should happen.
    controller.wait(500)
    assert len(state.pending_moves) == 2

    # Wait until t=1200. First move should execute.
    controller.wait(700)  # clock is now 1200
    assert len(state.pending_moves) == 1
    check_cell(board, 1, 1, "wP")
    check_cell(board, 0, 0, ".")


def test_click_edge_cases():
    board = Board(["wP .", ". bP"])
    controller, state = create_controller(board)

    # Click out of bounds
    controller.click(-100, 0)
    assert state.selected_piece is None

    # Click empty cell when nothing selected
    controller.click(150, 0)  # cell (0, 1) -> '.'
    assert state.selected_piece is None

    # Click non-empty cell -> selects it
    controller.click(50, 0)  # cell (0, 0) -> 'wP'
    assert state.selected_piece == board.get_piece_at(0, 0)

    # Click a friendly piece when another friendly is selected -> change selection
    board_friendly = Board(["wP wP", ". ."])
    controller_f, state_f = create_controller(board_friendly)
    controller_f.click(50, 0)   # selects (0, 0)
    assert state_f.selected_piece == board_friendly.get_piece_at(0, 0)
    controller_f.click(150, 0)  # clicks (0, 1) -> friendly wP
    assert state_f.selected_piece == board_friendly.get_piece_at(0, 1)  # selection updated!


def test_click_move_scheduling():
    # Use a board layout where white pawn (wP) at (1, 0) can legally move to (0, 0).
    board = Board([". .", "wP ."])
    controller, state = create_controller(board)

    # Click and select (1, 0)
    controller.click(50, 100)
    assert state.selected_piece == board.get_piece_at(1, 0)
    # Click (0, 0) -> schedules move
    controller.click(50, 0)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None
    assert state.pending_moves[0].from_pos == Cell(1, 0)
    assert state.pending_moves[0].to_pos == Cell(0, 0)


def test_click_move_scheduling_none_piece():
    board = Board([". .", "wP ."])
    controller, state = create_controller(board)
    # Click and select (1, 0)
    controller.click(50, 100)
    assert state.selected_piece == board.get_piece_at(1, 0)
    # Clear the board grid at that spot, so piece resolves to None
    board.grid[1][0] = None
    # Click (0, 0) -> schedules move with None piece and default duration 1000
    controller.click(50, 0)
    assert len(state.pending_moves) == 1
    assert state.pending_moves[0].piece is None
    assert state.pending_moves[0].arrival == 1000


def test_click_while_moving_or_reserved_tricked():
    class TrickList(list):
        def __bool__(self):
            return False

    board = Board(["wP wP", ". ."])
    controller, state = create_controller(board)

    # 1. Test clicking a cell that is currently moving (first check: cell_y, cell_x is moving)
    p = get_piece("wP")
    state.pending_moves = TrickList([PendingMove(Cell(0, 0), Cell(1, 0), p, 1000)])
    controller.click(50, 0)  # Click (0, 0) which is moving
    assert state.selected_piece is None

    # 2. Test selected piece is already in transit (third check: sel_y, sel_x is moving)
    state.selected_piece = board.get_piece_at(0, 0)
    controller.click(50, 100)  # Clicks (1, 0)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None

    # 3. Test destination is targeted by another pending move (fourth check: destination reserved)
    state.pending_moves = TrickList([PendingMove(Cell(0, 1), Cell(1, 0), p, 1000)])
    state.selected_piece = board.get_piece_at(0, 0)  # (0, 0) is not moving
    controller.click(50, 100)  # Click (1, 0) (destination is reserved)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None


def test_click_game_over_and_pending_moves_return():
    board = Board(["wP .", ". ."])
    controller, state = create_controller(board)
    state.game_over = True
    controller.click(50, 0)
    assert state.selected_piece is None

    state.game_over = False
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 1), MockSimplePiece("w"), 1000))
    controller.click(50, 0)
    assert state.selected_piece is None


def test_click_illegal_move_retains_selection():
    # Use a piece that fails rule validation
    board = Board(["wP .", ". ."])
    controller, state = create_controller(board)
    # Select (0, 0)
    controller.click(50, 0)
    assert state.selected_piece == board.get_piece_at(0, 0)
    # Move to illegal target coordinates (out of board)
    controller.click(950, 950)
    # Selection cancelled (out of board → cancel selection per spec)
    assert state.selected_piece is None
    assert len(state.pending_moves) == 0


def test_jump():
    board = Board(["wP .", ". ."])
    controller, state = create_controller(board)

    # Jump out of bounds
    controller.jump(-100, 0)
    assert len(state.jumps) == 0

    # Jump on empty cell
    controller.jump(150, 0)  # cell (0, 1) -> '.'
    assert len(state.jumps) == 0

    # Jump on moving piece (ignored)
    p = get_piece("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 0), p, 1000))
    controller.jump(50, 0)  # cell (0, 0)
    assert len(state.jumps) == 0

    # Jump on destination reserved cell (ignored)
    controller.jump(50, 100)  # cell (1, 0) -> reserved destination
    assert len(state.jumps) == 0

    # Valid jump
    state.pending_moves.clear()
    controller.jump(50, 0)
    assert len(state.jumps) == 1
    assert state.jumps[0].cell == (0, 0)
    assert state.jumps[0].start == 0
    assert state.jumps[0].end == 1000

    # Jump after game over (ignored)
    state.game_over = True
    state.jumps.clear()
    controller.jump(50, 0)
    assert len(state.jumps) == 0


def test_print_board():
    board = Board(["wP .", ". bP"])
    output = io.StringIO()
    controller, state = create_controller(board, stdout=output)
    controller.print_board()
    assert output.getvalue() == "wP .\n. bP\n"
