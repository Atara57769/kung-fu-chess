from models.game_state import GameState
from models.board import Board

def test_game_state_init():
    board = Board(["wK .", ". ."])
    state = GameState(board=board)
    assert state.board == board
    assert state.selected_piece is None
    assert state.game_over is False
    assert state.clock == 0
    assert state.pending_moves == []
    assert state.jumps == []
