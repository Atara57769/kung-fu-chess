import pytest
from models.board import Board
from services.board_parser import TextBoardParser
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece
from models.pending_move import PendingMove
from models.jump import Jump
from realtime.real_time_arbiter import RealTimeArbiter

def test_real_time_arbiter_clock():
    board = TextBoardParser().parse(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    assert state.clock == 0
    arbiter.tick(state, 100)
    assert state.clock == 100
    arbiter.tick(state, 250)
    assert state.clock == 350

def test_real_time_arbiter_move_execution():
    board = TextBoardParser().parse(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_king = board.get_piece_at(Cell(0, 0))
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_king, 200))
    
    arbiter.tick(state, 100)
    assert board.get_piece_at(Cell(0, 0)) == w_king
    assert board.get_piece_at(Cell(0, 1)) is None
    assert len(state.pending_moves) == 1
    
    arbiter.tick(state, 100)
    assert board.get_piece_at(Cell(0, 0)) is None
    assert board.get_piece_at(Cell(0, 1)) == w_king
    assert len(state.pending_moves) == 0

def test_real_time_arbiter_game_over_by_capture():
    board = TextBoardParser().parse(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_king = board.get_piece_at(Cell(0, 0))
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(1, 1), w_king, 100))
    
    assert state.game_over is False
    arbiter.tick(state, 100)
    assert board.get_piece_at(Cell(1, 1)) == w_king
    assert state.game_over is True

def test_real_time_arbiter_airborne_capture():
    board = TextBoardParser().parse(["wP .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_pawn = board.get_piece_at(Cell(0, 0))
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_pawn, 100))
    
    b_king = board.get_piece_at(Cell(1, 1))
    state.jumps.append(Jump((0, 1), 50, 150, b_king))
    
    arbiter.tick(state, 100)
    assert board.get_piece_at(Cell(0, 0)) is None
    assert board.get_piece_at(Cell(0, 1)) is None
    assert len(state.pending_moves) == 0

def test_real_time_arbiter_source_changes():
    board = TextBoardParser().parse(["wK .", ". bK"])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_king = board.get_piece_at(Cell(0, 0))
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), w_king, 100))
    
    w_king.cell = Cell(1, 0)
    board.grid[1][0] = w_king
    board.grid[0][0] = None
    
    arbiter.tick(state, 100)
    
    assert board.grid[1][0] is None
    assert board.grid[0][1] == w_king
    assert w_king.cell == Cell(0, 1)

def test_real_time_arbiter_escaping_king():
    board = TextBoardParser().parse(["wR . bK", ". . ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_rook = board.get_piece_at(Cell(0, 0))
    b_king = board.get_piece_at(Cell(0, 2))
    
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 2), w_rook, 100))
    state.pending_moves.append(PendingMove(Cell(0, 2), Cell(1, 2), b_king, 150))
    
    arbiter.tick(state, 100)
    assert state.game_over is False

def test_promotion():
    board = TextBoardParser().parse([". .", ". ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()

    p1 = Piece("w", "P", Cell(1, 0))
    board.grid[1][0] = p1
    move1 = PendingMove(Cell(1, 0), Cell(0, 0), p1, 1000)
    arbiter.apply_pawn_promotion(state, move1)
    arbiter.execute_move_on_board(state, move1)
    assert board.grid[0][0] == Piece("w", "Q", Cell(0, 0))

    board.grid = [[None, None], [None, None]]
    p2 = Piece("w", "P", Cell(0, 0))
    board.grid[0][0] = p2
    move2 = PendingMove(Cell(0, 0), Cell(1, 0), p2, 1000)
    arbiter.apply_pawn_promotion(state, move2)
    arbiter.execute_move_on_board(state, move2)
    assert board.grid[1][0] == Piece("w", "P", Cell(1, 0))

    board.grid = [[None, None], [None, None]]
    p3 = Piece("w", "N", Cell(1, 0))
    board.grid[1][0] = p3
    move3 = PendingMove(Cell(1, 0), Cell(0, 0), p3, 1000)
    arbiter.apply_pawn_promotion(state, move3)
    arbiter.execute_move_on_board(state, move3)
    assert board.grid[0][0] == Piece("w", "N", Cell(0, 0))

def test_game_over_service():
    from rules.win_condition import check_game_over
    board = TextBoardParser().parse(["wK bN", ". ."])
    state = GameState(board=board)

    assert check_game_over(state, Cell(0, 0)) is True
    assert check_game_over(state, Cell(0, 1)) is False
    assert check_game_over(state, Cell(1, 0)) is False

def test_execute_move_captured():
    board = TextBoardParser().parse(["wP .", ". ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=Piece("w", "P", Cell(0, 0)),
        arrival=1000
    )
    arbiter.execute_capture(state, move)
    assert board.grid[0][0] is None

    board2 = TextBoardParser().parse(["wP .", ". ."])
    state2 = GameState(board=board2)
    board2.grid[0][0] = None
    arbiter.execute_capture(state2, move)
    assert board2.grid[0][0] is None

def test_execute_move_success():
    board = TextBoardParser().parse(["wP .", ". ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 1),
        piece=board.get_piece_at(Cell(0, 0)),
        arrival=1000
    )
    arbiter.execute_move_on_board(state, move)
    assert board.grid[0][0] is None
    assert board.grid[1][1] == Piece("w", "P", Cell(1, 1))

def test_real_time_arbiter_coverage_edge_cases():
    board = TextBoardParser().parse(["wP .", ". ."])
    state = GameState(board=board)
    arb = RealTimeArbiter()

    p = Piece.from_text("wP")
    move = PendingMove(Cell(0, 0), Cell(0, 1), p, 1000)

    class TrickyPiece:
        def __init__(self):
            self._reads = 0
            self.kind = "P"
        @property
        def color(self):
            self._reads += 1
            if self._reads == 1:
                return "w"
            return "b"

    tricky = TrickyPiece()
    move_tricky = PendingMove(Cell(1, 0), Cell(0, 0), tricky, 1000)
    arb.apply_pawn_promotion(state, move_tricky)
    assert move_tricky.piece.kind == "Q"

def test_real_time_arbiter_cooldown_set():
    board = TextBoardParser().parse(["wR .", ". ."])
    state = GameState(board=board)
    arbiter = RealTimeArbiter()
    
    w_rook = board.get_piece_at(Cell(0, 0))
    move = PendingMove(Cell(0, 0), Cell(0, 1), w_rook, 1000)
    
    assert w_rook.cooldown_until == 0
    arbiter.process_move(state, move)
    assert w_rook.cooldown_until == 2000
