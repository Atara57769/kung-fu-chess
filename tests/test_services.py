import pytest
import io
import sys
from typing import Tuple, List, Optional
from models.pieces import Piece, PieceFactory
get_piece = PieceFactory.get_piece
from models.board import Board
from services.jump_service import JumpService
from models.jump import Jump
from models.cell import Cell
from models.pending_move import PendingMove
from models.game_state import GameState
from engine.controller import Controller
from engine.game_engine import GameEngine
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine


def create_state(board):
    return GameState(board=board)

def create_controller(board, stdout=sys.stdout):
    state = create_state(board)
    engine = GameEngine()
    return Controller(state, engine, stdout), state


def get_token(val):
    if isinstance(val, Piece):
        return val.color + val.kind
    return val or "."


# Mock piece for testing sub-service logic
class DummyPiece(Piece):
    def __init__(self, color: str, name_val: str = "P", is_king_val: bool = False, is_pawn_val: bool = False):
        kind = "K" if is_king_val else ("P" if is_pawn_val or name_val == "P" else "Q")
        if name_val == "R":
            kind = "R"
        elif name_val == "B":
            kind = "B"
        elif name_val == "N":
            kind = "N"
        super().__init__(color, kind)


def test_promotion():
    board = Board([". .", ". ."])
    state = create_state(board)
    arbiter = RealTimeArbiter()

    # White pawn promoting at y=0 on 2x2 board
    p1 = Piece("w", "P", Cell(1, 0))
    board.grid[1][0] = p1
    move1 = PendingMove(Cell(1, 0), Cell(0, 0), p1, 1000)
    arbiter.apply_pawn_promotion(state, move1)
    arbiter.execute_move_on_board(state, move1)
    assert board.grid[0][0] == Piece("w", "Q", Cell(0, 0))

    # White pawn not promoting at y=1 on 2x2 board
    board.grid = [[None, None], [None, None]]
    p2 = Piece("w", "P", Cell(0, 0))
    board.grid[0][0] = p2
    move2 = PendingMove(Cell(0, 0), Cell(1, 0), p2, 1000)
    arbiter.apply_pawn_promotion(state, move2)
    arbiter.execute_move_on_board(state, move2)
    assert board.grid[1][0] == Piece("w", "P", Cell(1, 0))

    # Non-pawn (knight) not promoting
    board.grid = [[None, None], [None, None]]
    p3 = Piece("w", "N", Cell(1, 0))
    board.grid[1][0] = p3
    move3 = PendingMove(Cell(1, 0), Cell(0, 0), p3, 1000)
    arbiter.apply_pawn_promotion(state, move3)
    arbiter.execute_move_on_board(state, move3)
    assert board.grid[0][0] == Piece("w", "N", Cell(0, 0))


def test_game_over_service():
    board = Board(["wK bN", ". ."])

    def get_piece_mock(token: str) -> Optional[Piece]:
        if token == "wK":
            return DummyPiece("w", is_king_val=True)
        if token == "bN":
            return DummyPiece("b", is_king_val=False)
        return None

    board.get_piece_at = lambda y, x: get_piece_mock(get_token(board.grid[y][x]))
    state = create_state(board)
    arbiter = RealTimeArbiter()

    assert arbiter.check_game_over(state, Cell(0, 0)) is True
    assert arbiter.check_game_over(state, Cell(0, 1)) is False
    assert arbiter.check_game_over(state, Cell(1, 0)) is False


def test_jump_service():
    board = Board([". ."])
    state = create_state(board)
    service = JumpService(state)
    p_white = DummyPiece("w")
    p_black = DummyPiece("b")

    # Schedule a jump at (2, 2) from t=100 to t=1100
    service.schedule_jump((2, 2), 100, p_white)

    # Airborne capture checking:
    # 1. Target Cell match, inside time window, opposite color -> Captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_black) is True

    # 2. Same color -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 500, p_white) is False

    # 3. Target Cell match, outside time window -> Not captured
    assert service.is_captured_by_airborne_enemy((2, 2), 1200, p_black) is False

    # 4. Target Cell mismatch -> Not captured
    assert service.is_captured_by_airborne_enemy((1, 1), 500, p_black) is False


def test_game_engine_schedule_move():
    """Tests that GameEngine.request_move appends a PendingMove with correct arrival."""
    board = Board([". .", "wP ."])
    state = create_state(board)
    engine = GameEngine()
    p = DummyPiece("w")

    engine.request_move(state, Cell(1, 0), Cell(0, 0))
    assert len(state.pending_moves) == 1
    assert state.pending_moves[0].arrival == 1000  # distance=1, DURATION=1000

    state.clock = 500
    state.pending_moves.clear()
    engine.request_move(state, Cell(1, 0), Cell(0, 0))
    assert state.pending_moves[0].arrival == 1500


def test_game_engine_wait_advances_clock():
    board = Board(["wP .", ". ."])
    state = create_state(board)
    engine = GameEngine()

    engine.wait(state, 500)
    assert state.clock == 500


def test_rule_engine_validation():
    board = Board(["wK .", ". ."])
    state = create_state(board)
    rule = RuleEngine()

    # is_within_bounds via board
    assert board.is_inside_bounds(0, 0) is True
    assert board.is_inside_bounds(-1, 0) is False
    assert board.is_inside_bounds(0, 2) is False

    # is_piece_moving and is_destination_reserved
    p = DummyPiece("w")
    state.pending_moves = [PendingMove(Cell(0, 0), Cell(1, 1), p, 1000)]

    assert rule.is_piece_moving(Cell(0, 0), state.pending_moves) is True
    assert rule.is_piece_moving(Cell(1, 1), state.pending_moves) is False
    assert rule.is_destination_reserved(Cell(0, 0), state.pending_moves) is False
    assert rule.is_destination_reserved(Cell(1, 1), state.pending_moves) is True


def test_controller_game_over_triggers():
    board = Board(["wP bK", ". ."])
    controller, state = create_controller(board)

    p_pawn = get_piece("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))

    # wait() causes game over
    controller.wait(1000)
    assert state.game_over is True

    # Reset and check print_board() does not trigger game over, but wait() does
    board2 = Board(["wP bK", ". ."])
    controller2, state2 = create_controller(board2, stdout=io.StringIO())
    state2.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state2.clock = 1000
    controller2.print_board()
    assert state2.game_over is False
    controller2.wait(0)
    assert state2.game_over is True

    # Reset and check jump() does not trigger game over, but wait() does
    board3 = Board(["wP bK", ". ."])
    controller3, state3 = create_controller(board3)
    state3.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state3.clock = 1000
    controller3.jump(0, 0)
    assert state3.game_over is False
    controller3.wait(0)
    assert state3.game_over is True


def test_controller_click_game_over():
    board = Board(["wP bK", ". ."])
    controller, state = create_controller(board)

    p_pawn = get_piece("wP")
    state.pending_moves.append(PendingMove(Cell(0, 0), Cell(0, 1), p_pawn, 1000))
    state.clock = 1000

    controller.click(50, 0)
    assert state.game_over is False
    controller.wait(0)
    assert state.game_over is True

    controller.click(50, 0)
    assert state.game_over is True


def test_game_engine_coverage_edge_cases():
    # 1. game_engine.request_move when game_over is True
    board = Board(["wP .", ". ."])
    state = create_state(board)
    state.game_over = True
    engine = GameEngine()
    engine.request_move(state, Cell(0, 0), Cell(0, 1))
    assert len(state.pending_moves) == 0

    # 2. game_engine.request_move edge cases (outside bounds, friendly dest, moving source, reserved dest, enemy is moving)
    # Re-enable game
    state.game_over = False
    p = get_piece("wP")
    # Outside bounds
    engine.request_move(state, Cell(0, 0), Cell(5, 5))
    assert len(state.pending_moves) == 0

    # Friendly destination
    board.grid[0][1] = get_piece("wP")
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
    board.grid[0][1] = get_piece("bP")
    state.pending_moves.append(PendingMove(Cell(0, 1), Cell(1, 1), get_piece("bP"), 1000))
    engine.request_move(state, Cell(0, 0), Cell(1, 0))
    assert len(state.pending_moves) == 1  # only the enemy pending move, ours was rejected
    state.pending_moves.clear()
    board.grid[0][1] = None

    # Source has a piece but the move is genuinely illegal (not matching piece rules)
    engine.request_move(state, Cell(0, 0), Cell(1, 1))  # wP cannot move diagonally to empty cell
    assert len(state.pending_moves) == 0

    # Knight distance calculation branch
    board_n = Board(["wN . .", ". . .", ". . ."])
    state_n = create_state(board_n)
    engine.request_move(state_n, Cell(0, 0), Cell(1, 2))  # valid N move
    assert len(state_n.pending_moves) == 1
    assert state_n.pending_moves[0].arrival == 3000  # distance = 1+2 = 3 * 1000


def test_jump_service_coverage_edge_cases():
    # 1. Default state initialization
    js = JumpService(None)
    assert js.state is not None
    assert isinstance(js.state.board, Board)

    # 2. setter for jumps property
    state = create_state(Board([". ."]))
    js2 = JumpService(state)
    my_jumps = [Jump((0, 0), 0, 1000, get_piece("wP"))]
    js2.jumps = my_jumps
    assert js2.jumps == my_jumps


def test_real_time_arbiter_coverage_edge_cases():
    # Test pawn promotion fallback when move.piece matches color/kind check but current_piece at from_pos does not (i.e. is None or mismatch)
    board = Board(["wP .", ". ."])
    state = create_state(board)
    arb = RealTimeArbiter()

    # Place pawn at (0, 0)
    p = get_piece("wP")
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


def test_main_empty_command_coverage():
    # Test empty line in commands section does not break main/execute_commands
    board = Board(["wP .", ". ."])
    from main import execute_commands
    # Simply verify running it does not raise any exceptions
    execute_commands(board, ["", "   "])

