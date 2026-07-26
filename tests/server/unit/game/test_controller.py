import pytest
import io
import sys
from shared.models.board import Board
from server.game.services.board_parser import TextBoardParser
from shared.models.game_state import GameState
from shared.models.cell import Cell
from shared.models.pieces import Piece, PieceStatus
from shared.models.pending_move import PendingMove
from server.game.engine.controller import Controller
from server.game.engine.game_engine import GameEngine
from shared.models.color import Color

def create_state(board):
    return GameState(board=board)

def create_controller(board, stdout=sys.stdout):
    state = create_state(board)
    engine = GameEngine()
    return Controller(state, engine, stdout), state

def test_move_edge_cases():
    board = TextBoardParser().parse(["wP .", ". bP"])
    controller, state = create_controller(board)

    # Move out of bounds
    controller.move(None, Cell(0, 1))
    assert len(state.pending_moves) == 0

    controller.move(Cell(0, 0), Cell(10, 10))
    assert len(state.pending_moves) == 0

    # Move empty cell
    controller.move(Cell(0, 1), Cell(1, 1))
    assert len(state.pending_moves) == 0

def test_move_scheduling():
    board = TextBoardParser().parse([". .", "wP ."])
    controller, state = create_controller(board)

    # Move (1, 0) to (0, 0) -> schedules move
    controller.move(Cell(1, 0), Cell(0, 0))
    assert len(state.pending_moves) == 1
    assert state.pending_moves[0].from_pos == Cell(1, 0)
    assert state.pending_moves[0].to_pos == Cell(0, 0)

def test_move_while_moving():
    board = TextBoardParser().parse(["wP wP", ". ."])
    controller, state = create_controller(board)

    p = board.get_piece_at(Cell(0, 0))
    p.status = PieceStatus.MOVING
    state.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 0), p, 1000)]

    # Attempt to move a piece that is already moving -> ignored
    controller.move(Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1

def test_move_game_over():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    state.game_over = True

    controller.move(Cell(0, 0), Cell(1, 0))
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
    controller.jump(Cell(0, 0))
    assert len(state.jumps) == 0

    # Valid jump
    state.pending_moves.clear()
    p.status = PieceStatus.IDLE
    controller.jump(Cell(0, 0))
    assert len(state.jumps) == 1
    assert state.jumps[0].cell == (0, 0)

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

def test_controller_wait_and_snapshot():
    board = TextBoardParser().parse(["wP .", ". ."])
    controller, state = create_controller(board)
    assert state.clock == 0
    controller.wait(100)
    assert state.clock == 100
    
    snap = controller.get_snapshot()
    assert snap.clock == 100

def test_controller_player_color_restrictions():
    board = TextBoardParser().parse(["wP .", ". bR"])

    controller, state = create_controller(board)

    # 1. White player attempts to move black piece -> ignored
    controller.move(Cell(1, 1), Cell(1, 0), player_color=Color.WHITE)
    assert len(state.pending_moves) == 0

    # 2. Black player moves black piece -> works
    controller.move(Cell(1, 1), Cell(1, 0), player_color=Color.BLACK)
    assert len(state.pending_moves) == 1

    # 3. Jump restrictions: White jumps black piece -> ignored
    controller.jump(Cell(1, 1), player_color=Color.WHITE)
    assert len(state.jumps) == 0

    # White jumps white piece -> works
    controller.jump(Cell(0, 0), player_color=Color.WHITE)
    assert len(state.jumps) == 1
