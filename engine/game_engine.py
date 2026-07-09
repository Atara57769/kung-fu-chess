from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from models.pending_move import PendingMove
from constants import DURATION


class GameEngine:
    """Stateless engine that operates exclusively on GameState."""

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

        from rules.rule_engine import RuleEngine
        rule = RuleEngine()
        board = state.board
        pending = state.pending_moves

        if rule.outside_board(board, from_cell, to_cell):
            return
        if rule.friendly_destination(board, from_cell, to_cell):
            return
        if rule.is_piece_moving(from_cell, pending):
            return
        if rule.is_destination_reserved(to_cell, pending):
            return
        if rule.enemy_is_moving(board, from_cell, pending):
            return
        if not rule.illegal_to_move(board, from_cell, to_cell):
            # illegal_to_move returns False when source is empty — allow that case
            piece_at_src = board.get_piece_at(from_cell.y, from_cell.x)
            if piece_at_src is not None:
                # Source has a piece but the move is genuinely illegal
                return
            # Source is empty — allow scheduling with piece=None

        piece = state.board.get_piece_at(from_cell.y, from_cell.x)

        dy = to_cell.y - from_cell.y
        dx = to_cell.x - from_cell.x
        if piece is not None and piece.kind == 'N':
            distance = abs(dy) + abs(dx)
        else:
            distance = max(abs(dy), abs(dx))

        duration = distance * DURATION
        arrival = state.clock + duration

        state.pending_moves.append(PendingMove(
            from_pos=from_cell,
            to_pos=to_cell,
            piece=piece,
            arrival=arrival,
        ))

    def wait(self, state: GameState, ms: int) -> None:
        """Advances the clock and processes any completed moves."""
        from realtime.real_time_arbiter import RealTimeArbiter
        RealTimeArbiter().tick(state, ms)

    def jump(self, state: GameState, cell: Cell) -> None:
        """Schedules a jump for the piece at the given cell."""
        from services.jump_service import JumpService
        if not self.can_jump(state, cell):
            return
        piece = state.board.get_piece_at(cell.y, cell.x)
        JumpService(state).schedule_jump(
            cell=(cell.y, cell.x),
            start_time=state.clock,
            piece=piece,
        )

    def print_board(self, state: GameState, stdout) -> None:
        """Prints the board in canonical space-separated format."""
        from output.board_printer import print_board
        print_board(state.board, stdout=stdout)

    def is_piece_moving(self, state: GameState, cell: Cell) -> bool:
        """Returns True if the piece at cell is the source of a pending move."""
        from rules.rule_engine import RuleEngine
        return RuleEngine().is_piece_moving(cell, state.pending_moves)

    def can_jump(self, state: GameState, cell: Cell) -> bool:
        """Returns True if a jump on cell is currently allowed."""
        from rules.rule_engine import RuleEngine
        rule = RuleEngine()
        pending = state.pending_moves
        return not rule.is_piece_moving(cell, pending) and not rule.is_destination_reserved(cell, pending)
