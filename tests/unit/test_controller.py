import pytest
import io
import sys
from models.board import Board
from services.board_parser import TextBoardParser
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece, PieceStatus
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
    controller.click(None)
    assert state.selected_piece is None

    # Click empty cell when nothing selected
    controller.click(Cell(0, 1))  # cell (0, 1) -> '.'
    assert state.selected_piece is None

    # Click non-empty cell -> selects it
    controller.click(Cell(0, 0))  # cell (0, 0) -> 'wP'
    assert state.selected_piece == board.get_piece_at(Cell(0, 0))

    # Click a friendly piece when another friendly is selected -> change selection
    board_friendly = TextBoardParser().parse(["wP wP", ". ."])
    controller_f, state_f = create_controller(board_friendly)
    controller_f.click(Cell(0, 0))   # selects (0, 0)
    assert state_f.selected_piece == board_friendly.get_piece_at(Cell(0, 0))
    controller_f.click(Cell(0, 1))  # clicks (0, 1) -> friendly wP
    assert state_f.selected_piece == board_friendly.get_piece_at(Cell(0, 1))

def test_click_move_scheduling():
    board = TextBoardParser().parse([". .", "wP ."])
    controller, state = create_controller(board)

    # Click and select (1, 0)
    controller.click(Cell(1, 0))
    assert state.selected_piece == board.get_piece_at(Cell(1, 0))
    # Click (0, 0) -> schedules move
    controller.click(Cell(0, 0))
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None
    assert state.pending_moves[0].from_pos == Cell(1, 0)
    assert state.pending_moves[0].to_pos == Cell(0, 0)

def test_click_move_scheduling_none_piece():
    board = TextBoardParser().parse([". .", "wP ."])
    controller, state = create_controller(board)
    # Click and select (1, 0)
    controller.click(Cell(1, 0))
    assert state.selected_piece == board.get_piece_at(Cell(1, 0))
    # Clear the board grid at that spot, so piece resolves to None
    board.grid[1][0] = None
    # Click (0, 0) -> should NOT schedule move since empty source is illegal
    controller.click(Cell(0, 0))
    assert len(state.pending_moves) == 0

def test_click_selected_piece_killed_before_second_click():
    board = TextBoardParser().parse(["wP .", ". bP"])
    controller, state = create_controller(board)
    
    # Click and select (0, 0)
    controller.click(Cell(0, 0))
    wP = board.get_piece_at(Cell(0, 0))
    assert state.selected_piece == wP
    
    # Simulate that the selected piece was killed before the second click
    # (e.g. bP moved to (0, 0) and captured it)
    bP = board.get_piece_at(Cell(1, 1))
    board.grid[0][0] = bP
    bP.cell = Cell(0, 0)
    
    # Click (0, 1) -> second click
    controller.click(Cell(0, 1))
    
    # Assert selection is reset and no move is scheduled
    assert state.selected_piece is None
    assert len(state.pending_moves) == 0

def test_click_selected_piece_killed_to_none_before_second_click():
    board = TextBoardParser().parse(["wP .", ". bP"])
    controller, state = create_controller(board)
    
    # Click and select (0, 0)
    controller.click(Cell(0, 0))
    wP = board.get_piece_at(Cell(0, 0))
    assert state.selected_piece == wP
    
    # Simulate that the selected piece was killed and cell became None
    board.grid[0][0] = None
    
    # Click (0, 1) -> second click
    controller.click(Cell(0, 1))
    
    # Assert selection is reset and no move is scheduled
    assert state.selected_piece is None
    assert len(state.pending_moves) == 0

def test_click_while_moving_or_reserved():
    board = TextBoardParser().parse(["wP wP", ". ."])
    controller, state = create_controller(board)

    # 1. Test clicking a cell that is currently moving (first check: cell_y, cell_x is moving)
    p = board.get_piece_at(Cell(0, 0))
    p.status = PieceStatus.MOVING
    state.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 0), p, 1000)]
    controller.click(Cell(0, 0))  # Click (0, 0) which is moving
    assert state.selected_piece is None

    # 2. Test selected piece is already in transit (third check: sel_y, sel_x is moving)
    state.selected_piece = board.get_piece_at(Cell(0, 0))
    controller.click(Cell(1, 0))  # Clicks (1, 0)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None

    # 3. Test destination is targeted by another pending move (fourth check: destination reserved)
    state.pending_moves = [PendingMove(Cell(0, 1), Cell(1, 0), p, 1000)]
    state.selected_piece = board.get_piece_at(Cell(0, 0))  # (0, 0) is not moving
    controller.click(Cell(1, 0))  # Click (1, 0) (destination is reserved)
    assert len(state.pending_moves) == 1
    assert state.selected_piece is None

def test_click_game_over_and_pending_moves_return():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    state.game_over = True
    controller.click(Cell(0, 0))
    assert state.selected_piece is None

    state.game_over = False
    p = board.get_piece_at(Cell(0, 0))
    p.status = PieceStatus.MOVING
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 1), p, 1000))
    controller.click(Cell(0, 0))
    assert state.selected_piece is None

def test_click_illegal_move_retains_selection():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    # Select (0, 0)
    controller.click(Cell(0, 0))
    assert state.selected_piece == board.get_piece_at(Cell(0, 0))
    # Move to illegal target coordinates (out of board)
    controller.click(None)
    # Selection cancelled (out of board)
    assert state.selected_piece is None
    assert len(state.pending_moves) == 0

def test_jump():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)

    # Jump out of bounds
    controller.jump(None)
    assert len(state.jumps) == 0

    # Jump on empty cell
    controller.jump(Cell(0, 1))  # cell (0, 1) -> '.'
    assert len(state.jumps) == 0

    # Jump on moving piece (ignored)
    p = board.get_piece_at(Cell(0, 0))
    p.status = PieceStatus.MOVING
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 0), p, 1000))
    controller.jump(Cell(0, 0))  # cell (0, 0)
    assert len(state.jumps) == 0

    # Jump on destination reserved cell (ignored)
    controller.jump(Cell(1, 0))  # cell (1, 0) -> reserved destination
    assert len(state.jumps) == 0

    # Valid jump
    state.pending_moves.clear()
    p.status = PieceStatus.IDLE
    controller.jump(Cell(0, 0))
    assert len(state.jumps) == 1
    assert state.jumps[0].cell == (0, 0)
    assert state.jumps[0].start == 0
    assert state.jumps[0].end == 1000

    # Jump after game over (ignored)
    state.game_over = True
    state.jumps.clear()
    controller.jump(Cell(0, 0))
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
    p_pawn = Piece.from_text("wP")
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
    controller3.jump(Cell(0, 0))
    assert state3.game_over is False
    controller3.wait(0)
    assert state3.game_over is True

def test_controller_click_game_over():
    board = TextBoardParser().parse(["wP bK", ". ."])
    controller, state = create_controller(board)
    p_pawn = Piece.from_text("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state.clock = 1000

    controller.click(Cell(0, 0))
    assert state.game_over is False
    controller.wait(0)
    assert state.game_over is True

    controller.click(Cell(0, 0))
    assert state.game_over is True

def test_controller_click_moving_friendly_piece():
    board = TextBoardParser().parse(["wR wP", ". ."])
    controller, state = create_controller(board)
    
    # Select first friendly piece (0, 0)
    controller.click(Cell(0, 0))
    assert state.selected_piece == board.get_piece_at(Cell(0, 0))
    
    # Mark second friendly piece (0, 1) as moving
    p2 = board.get_piece_at(Cell(0, 1))
    p2.status = PieceStatus.MOVING
    state.pending_moves.append(PendingMove(Cell(0, 1), Cell(1, 1), p2, 1000))
    
    # Click second friendly piece (0, 1), which is moving
    controller.click(Cell(0, 1))
    # The selection should be cleared (None)
    assert state.selected_piece is None
    # A new pending move from (0, 0) to (0, 1) should be requested/scheduled
    assert len(state.pending_moves) == 2
    assert state.pending_moves[1].from_pos == Cell(0, 0)
    assert state.pending_moves[1].to_pos == Cell(0, 1)

