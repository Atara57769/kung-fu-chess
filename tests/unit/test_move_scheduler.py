import pytest
from models.game_state import GameState
from models.board import Board
from models.cell import Cell
from models.pieces import Piece
from services.move_scheduler import MoveScheduler

def test_move_scheduler_create_and_add():
    board = Board([[None]*3 for _ in range(3)], 3, 3)
    state = GameState(board=board)
    scheduler = MoveScheduler()

    piece = Piece("w", "P", Cell(1, 0))
    move = scheduler.create_pending_move(
        from_cell=Cell(1, 0),
        to_cell=Cell(0, 0),
        piece=piece,
        arrival=1000,
        is_captured=True
    )

    assert move.from_pos == Cell(1, 0)
    assert move.to_pos == Cell(0, 0)
    assert move.piece == piece
    assert move.arrival == 1000
    assert move.is_captured is True

    assert len(state.pending_moves) == 0
    scheduler.add_to_pending(state, move)
    assert len(state.pending_moves) == 1
    assert state.pending_moves[0] == move
