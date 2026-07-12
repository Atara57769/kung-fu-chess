from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from models.pending_move import PendingMove
from constants import DURATION, PIECE_KNIGHT
from rules.rule_engine import RuleEngine
from services.collision_service import CollisionService
from realtime.real_time_arbiter import RealTimeArbiter
from services.jump_service import JumpService
        

class GameEngine:
    """Stateless engine that operates exclusively on GameState."""

    def __init__(self, rule_engine=None, collision_service=None, real_time_arbiter=None, jump_service=None):
        self.rule_engine = rule_engine or RuleEngine()
        self.collision_service = collision_service or CollisionService()
        self.real_time_arbiter = real_time_arbiter or RealTimeArbiter()
        self.jump_service = jump_service or JumpService()

    def request_move(self, state: GameState, from_cell: Cell, to_cell: Cell) -> None:
        """
        Validates and schedules a move from from_cell to to_cell.
        Does nothing if the game is over or the move is illegal.
        Mirrors the original validate_move logic: checks bounds, friendly destination,
        transit/reservation, enemy-moving, and piece legality — but does NOT require
        the source cell to be non-empty (the Controller already confirmed selection).
        """
        if state.game_over:
            return

        board = state.board
        pending = state.pending_moves

        if not self.rule_engine.is_move_valid(board, from_cell, to_cell, pending):
            return

        piece = state.board.get_piece_at(from_cell)
        if piece is not None and piece.cooldown_until > state.clock:
            return

        duration = self.collision_service.get_move_duration(from_cell, to_cell, piece)
        arrival = state.clock + duration

        self.schedule_move(state, from_cell, to_cell, piece, arrival)

    def schedule_move(self, state: GameState, from_cell: Cell, to_cell: Cell, piece: Optional[object], arrival: int) -> None:
        new_move = PendingMove(
            from_pos=from_cell,
            to_pos=to_cell,
            piece=piece,
            arrival=arrival,
        )
        if self.collision_service.check_mid_move_collision(state, new_move):
            new_move.is_captured = True
        state.pending_moves.append(new_move)

    def wait(self, state: GameState, ms: int) -> None:
        """Advances the clock and processes any completed moves."""
        self.real_time_arbiter.tick(state, ms)

    def jump(self, state: GameState, cell: Cell) -> None:
        """Schedules a jump for the piece at the given cell."""
        if not self.can_jump(state, cell):
            return
        piece = state.board.get_piece_at(cell)
        self.jump_service.schedule_jump(
            state=state,
            cell=(cell.y, cell.x),
            start_time=state.clock,
            piece=piece,
        )

    def print_board(self, state: GameState, stdout) -> None:
        """Prints the board in canonical space-separated format."""
        from services.board_printer import print_board
        print_board(state.board, stdout=stdout)

    def is_piece_moving(self, state: GameState, cell: Cell) -> bool:
        """Returns True if the piece at cell is the source of a pending move."""
        return self.rule_engine.is_piece_moving(cell, state.pending_moves)

    def can_jump(self, state: GameState, cell: Cell) -> bool:
        """Returns True if a jump on cell is currently allowed."""
        pending = state.pending_moves
        piece = state.board.get_piece_at(cell)
        if piece is not None and piece.cooldown_until > state.clock:
            return False
        return not self.rule_engine.is_piece_moving(cell, pending) and not self.rule_engine.board_rules.is_destination_reserved(cell, pending)
