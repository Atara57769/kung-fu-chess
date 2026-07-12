import pytest
import io
import sys
from models.board import Board
from services.board_parser import TextBoardParser
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece
from factory import PieceFactory
from models.pending_move import PendingMove
from engine.controller import Controller
from engine.game_engine import GameEngine

def create_state(board):
    return GameState(board=board)

def create_controller(board, stdout=sys.stdout):
    state = create_state(board)
    engine = GameEngine()
    return Controller(state, engine, stdout), state

def test_click_edge_cases():
    board = TextBoardParser().parse(["wP .", ". bP"])
    controller, state = create_controller(board)

    # Click out of bounds
    controller.click(-100, 0)
    assert state.selected_piece is None

    # Click empty cell when nothing selected
    controller.click(150, 0)  # cell (0, 1) -> '.'
    assert state.selected_piece is None

    # Click non-empty cell -> selects it
    controller.click(50, 0)  # cell (0, 0) -> 'wP'
    assert state.selected_piece == board.get_piece_at(Cell(0, 0))

    # Click a friendly piece when another friendly is selected -> change selection
    board_friendly = TextBoardParser().parse(["wP wP", ". ."])
    controller_f, state_f = create_controller(board_friendly)
    controller_f.click(50, 0)   # selects (0, 0)
    assert state_f.selected_piece == board_friendly.get_piece_at(Cell(0, 0))
    controller_f.click(150, 0)  # clicks (0, 1) -> friendly wP
    assert state_f.selected_piece == board_friendly.get_piece_at(Cell(0, 1))

def test_click_move_scheduling():
    board = TextBoardParser().parse([". .", "wP ."])
    controller, state = create_controller(board)

    # Click and select (1, 0)
    controller.click(50, 100)
    assert state.selected_piece == board.get_piece_at(Cell(1, 0))
    # Click (0, 0) -> schedules move
    controller.click(50, 0)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None
    assert state.pending_moves[0].from_pos == Cell(1, 0)
    assert state.pending_moves[0].to_pos == Cell(0, 0)

def test_click_move_scheduling_none_piece():
    board = TextBoardParser().parse([". .", "wP ."])
    controller, state = create_controller(board)
    # Click and select (1, 0)
    controller.click(50, 100)
    assert state.selected_piece == board.get_piece_at(Cell(1, 0))
    # Clear the board grid at that spot, so piece resolves to None
    board.grid[1][0] = None
    # Click (0, 0) -> should NOT schedule move since empty source is illegal
    controller.click(50, 0)
    assert len(state.pending_moves) == 0

def test_click_while_moving_or_reserved():
    board = TextBoardParser().parse(["wP wP", ". ."])
    controller, state = create_controller(board)

    # 1. Test clicking a cell that is currently moving (first check: cell_y, cell_x is moving)
    p = PieceFactory.from_text("wP")
    state.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 0), p, 1000)]
    controller.click(50, 0)  # Click (0, 0) which is moving
    assert state.selected_piece is None

    # 2. Test selected piece is already in transit (third check: sel_y, sel_x is moving)
    state.selected_piece = board.get_piece_at(Cell(0, 0))
    controller.click(50, 100)  # Clicks (1, 0)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None

    # 3. Test destination is targeted by another pending move (fourth check: destination reserved)
    state.pending_moves = [PendingMove(Cell(0, 1), Cell(1, 0), p, 1000)]
    state.selected_piece = board.get_piece_at(Cell(0, 0))  # (0, 0) is not moving
    controller.click(50, 100)  # Click (1, 0) (destination is reserved)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None

def test_click_game_over_and_pending_moves_return():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    state.game_over = True
    controller.click(50, 0)
    assert state.selected_piece is None

    state.game_over = False
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 1), PieceFactory.from_text("wP"), 1000))
    controller.click(50, 0)
    assert state.selected_piece is None

def test_click_illegal_move_retains_selection():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    # Select (0, 0)
    controller.click(50, 0)
    assert state.selected_piece == board.get_piece_at(Cell(0, 0))
    # Move to illegal target coordinates (out of board)
    controller.click(950, 950)
    # Selection cancelled (out of board)
    assert state.selected_piece is None
    assert len(state.pending_moves) == 0

def test_jump():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)

    # Jump out of bounds
    controller.jump(-100, 0)
    assert len(state.jumps) == 0

    # Jump on empty cell
    controller.jump(150, 0)  # cell (0, 1) -> '.'
    assert len(state.jumps) == 0

    # Jump on moving piece (ignored)
    p = PieceFactory.from_text("wP")
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
    board = TextBoardParser().parse(["wP .", ". bP"])
    output = io.StringIO()
    controller, state = create_controller(board, stdout=output)
    controller.print_board()
    assert output.getvalue() == "wP .\n. bP\n"

def test_controller_game_over_triggers():
    board = TextBoardParser().parse(["wP bK", ". ."])
    controller, state = create_controller(board)
    p_pawn = PieceFactory.from_text("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))

    # wait() causes game over
    controller.wait(1000)
    assert state.game_over is True

    # Reset and check print_board() does not trigger game over, but wait() does
    board2 = TextBoardParser().parse(["wP bK", ". ."])
    controller2, state2 = create_controller(board2, stdout=io.StringIO())
    state2.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state2.clock = 1000
    controller2.print_board()
    assert state2.game_over is False
    controller2.wait(0)
    assert state2.game_over is True

    # Reset and check jump() does not trigger game over, but wait() does
    board3 = TextBoardParser().parse(["wP bK", ". ."])
    controller3, state3 = create_controller(board3)
    state3.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state3.clock = 1000
    controller3.jump(0, 0)
    assert state3.game_over is False
    controller3.wait(0)
    assert state3.game_over is True

def test_controller_click_game_over():
    board = TextBoardParser().parse(["wP bK", ". ."])
    controller, state = create_controller(board)
    p_pawn = PieceFactory.from_text("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state.clock = 1000

    controller.click(50, 0)
    assert state.game_over is False
    controller.wait(0)
    assert state.game_over is True

    controller.click(50, 0)
    assert state.game_over is True
