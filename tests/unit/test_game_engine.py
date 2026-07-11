import pytest
from models.board import Board
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece, PieceFactory
from models.pending_move import PendingMove
from models.jump import Jump
from engine.game_engine import GameEngine
from services.jump_service import JumpService

def test_game_engine_schedule_move():
    board = Board([". .", "wP ."])
    state = GameState(board=board)
    engine = GameEngine()

    engine.request_move(state, Cell(1, 0), Cell(0, 0))
    assert len(state.pending_moves) == 1
    assert state.pending_moves[0].arrival == 1000  # distance=1, DURATION=1000

    state.clock = 500
    state.pending_moves.clear()
    engine.request_move(state, Cell(1, 0), Cell(0, 0))
    assert state.pending_moves[0].arrival == 1500

def test_game_engine_wait_advances_clock():
    board = Board(["wP .", ". ."])
    state = GameState(board=board)
    engine = GameEngine()

    engine.wait(state, 500)
    assert state.clock == 500

def test_game_engine_coverage_edge_cases():
    # 1. game_engine.request_move when game_over is True
    board = Board(["wP .", ". ."])
    state = GameState(board=board)
    state.game_over = True
    engine = GameEngine()
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0

    # 2. game_engine.request_move edge cases
    state.game_over = False
    p = PieceFactory.get_piece("wP")
    # Outside bounds
    engine.request_move(state, Cell(0, 0), Cell(5, 5))
    assert len(state.pending_moves) == 0

    # Friendly destination
    board.grid[0][1] = PieceFactory.get_piece("wP")
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0
    board.grid[0][1] = None

    # Source is already moving
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 0), p, 1000))
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()

    # Destination is reserved
    state.pending_moves.append(PendingMove(Cell(1, 0), Cell(0, 1), p, 1000))
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()

    # Enemy is moving
    board.grid[0][1] = PieceFactory.get_piece("bP")
    state.pending_moves.append(PendingMove(Cell(0, 1), Cell(1, 1), PieceFactory.get_piece("bP"), 1000))
    engine.request_move(state, Cell(0, 0), Cell(1, 0))
    assert len(state.pending_moves) == 1
    state.pending_moves.clear()
    board.grid[0][1] = None

    # Source has a piece but the move is genuinely illegal
    engine.request_move(state, Cell(0, 0), Cell(1, 1))
    assert len(state.pending_moves) == 0

    # Knight distance calculation branch
    board_n = Board(["wN . .", ". . .", ". . ."])
    state_n = GameState(board=board_n)
    engine.request_move(state_n, Cell(0, 0), Cell(1, 2))
    assert len(state_n.pending_moves) == 1
    assert state_n.pending_moves[0].arrival == 3000

def test_jump_service():
    board = Board([". ."])
    state = GameState(board=board)
    service = JumpService(state)
    p_white = PieceFactory.get_piece("wP")

    service.schedule_jump((2, 2), 100, p_white)
    assert len(service.jumps) == 1
    assert service.jumps[0].cell == (2, 2)

def test_jump_service_coverage_edge_cases():
    js = JumpService(None)
    assert js.state is not None
    assert isinstance(js.state.board, Board)

    state = GameState(board=Board([". ."]))
    js2 = JumpService(state)
    my_jumps = [Jump((0, 0), 0, 1000, PieceFactory.get_piece("wP"))]
    js2.jumps = my_jumps
    assert js2.jumps == my_jumps
