import logging
from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from models.pending_move import PendingMove
from constants import DURATION, PIECE_KNIGHT
from rules.rule_engine import RuleEngine
from services.collision_service import CollisionService
from realtime.real_time_arbiter import RealTimeArbiter
from services.jump_service import JumpService
from models.game_snapshot import GameSnapshot
        
logger = logging.getLogger(__name__)


class GameEngine:
    """Stateless engine that operates exclusively on GameState."""

    def __init__(self, rule_engine=None, collision_service=None, real_time_arbiter=None, jump_service=None):
        self.rule_engine = rule_engine or RuleEngine()
        self.collision_service = collision_service or CollisionService()
        self.real_time_arbiter = real_time_arbiter or RealTimeArbiter()
        self.jump_service = jump_service or JumpService()
        logger.debug("GameEngine initialized.")

    def snapshot(self, state: GameState) -> GameSnapshot:
        """Creates and returns a read-only snapshot of the game state."""
        logger.debug("Creating game state snapshot.")
        return GameSnapshot.from_state(state)

    def request_move(self, state: GameState, from_cell: Cell, to_cell: Cell) -> None:
        """
        Validates and schedules a move from from_cell to to_cell.
        Does nothing if the game is over or the move is illegal.
        Mirrors the original validate_move logic: checks bounds, friendly destination,
        transit/reservation, enemy-moving, and piece legality — but does NOT require
        the source cell to be non-empty (the Controller already confirmed selection).
        """
        if state.game_over:
            logger.info("request_move ignored: game is over.")
            return

        board = state.board
        pending = state.pending_moves

        if not self.rule_engine.is_move_valid(board, from_cell, to_cell, pending):
            logger.info(f"Move from {from_cell} to {to_cell} is invalid according to rule engine.")
            return

        piece = state.board.get_piece_at(from_cell)
        if piece is not None and piece.cooldown_until > state.clock:
            logger.info(f"Move from {from_cell} to {to_cell} ignored: piece is on cooldown until {piece.cooldown_until} (clock: {state.clock}).")
            return

        duration = self.collision_service.get_move_duration(from_cell, to_cell, piece)
        arrival = state.clock + duration

        self.schedule_move(state, from_cell, to_cell, piece, arrival)

    def schedule_move(self, state: GameState, from_cell: Cell, to_cell: Cell, piece: Optional[object], arrival: int) -> None:
        logger.info(f"Scheduling move for {piece} from {from_cell} to {to_cell} (arrival: {arrival})")
        new_move = PendingMove(
            from_pos=from_cell,
            to_pos=to_cell,
            piece=piece,
            arrival=arrival,
        )
        if self.collision_service.check_mid_move_collision(state, new_move):
            logger.info(f"Collision detected for new move: {new_move}")
            new_move.is_captured = True
        state.pending_moves.append(new_move)

    def wait(self, state: GameState, ms: int) -> None:
        """Advances the clock and processes any completed moves."""
        logger.debug(f"GameEngine advancing wait by {ms} ms")
        self.real_time_arbiter.tick(state, ms)

    def jump(self, state: GameState, cell: Cell) -> None:
        """Schedules a jump for the piece at the given cell."""
        if not self.can_jump(state, cell):
            logger.info(f"Jump not allowed at cell {cell}")
            return
        piece = state.board.get_piece_at(cell)
        logger.info(f"Scheduling jump for {piece} at cell {cell} starting at {state.clock}")
        self.jump_service.schedule_jump(
            state=state,
            cell=(cell.y, cell.x),
            start_time=state.clock,
            piece=piece,
        )

    def print_board(self, state: GameState, stdout) -> None:
        """Prints the board in canonical space-separated format."""
        from services.board_printer import print_board
        logger.debug("Routing print board to print_board service.")
        print_board(state.board, stdout=stdout)

    def is_piece_moving(self, state: GameState, cell: Cell) -> bool:
        """Returns True if the piece at cell is the source of a pending move."""
        moving = self.rule_engine.is_piece_moving(cell, state.pending_moves)
        logger.debug(f"Checking if piece at {cell} is moving: {moving}")
        return moving

    def can_jump(self, state: GameState, cell: Cell) -> bool:
        """Returns True if a jump on cell is currently allowed."""
        pending = state.pending_moves
        piece = state.board.get_piece_at(cell)
        if piece is not None and piece.cooldown_until > state.clock:
            logger.debug(f"Cannot jump: piece at {cell} is on cooldown.")
            return False
        is_moving = self.rule_engine.is_piece_moving(cell, pending)
        is_reserved = self.rule_engine.board_rules.is_destination_reserved(cell, pending)
        allowed = not is_moving and not is_reserved
        logger.debug(f"Checking can_jump for cell {cell}: is_moving={is_moving}, is_reserved={is_reserved} -> allowed={allowed}")
        return allowed
