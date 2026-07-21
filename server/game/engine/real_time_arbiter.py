import logging
from typing import Optional
from shared.models.game_state import GameState
from shared.models.pending_move import PendingMove
from shared.models.cell import Cell
from shared.models.pieces import Piece, PieceStatus
from shared.models.piece_type import PieceType
from shared.models.color import Color
from constants import COOLDOWN_MOVE
from server.game.rules.win_condition import check_game_over
from server.game.rules.promotion import PawnPromotion

logger = logging.getLogger(__name__)

class RealTimeArbiter:
    def __init__(self, promotion_service=None) -> None:
        self.promotion_service = promotion_service or PawnPromotion()

    def advance_clock(self, game_state: GameState, ms: int) -> None:
        """Advances the clock of the game state by the given milliseconds."""
        game_state.clock += ms

    def is_captured_by_airborne_enemy(self, game_state: GameState, move: PendingMove) -> bool:
        """Checks if the destination cell contains an active airborne enemy piece."""
        to_y, to_x = move.to_pos.y, move.to_pos.x
        for jump in game_state.jumps:
            if jump.cell == (to_y, to_x) and jump.start <= move.arrival <= jump.end:
                if jump.piece.color != move.piece.color:
                    return True
        return False

    def execute_capture(self, game_state: GameState, move: PendingMove) -> None:
        """Handles the capture of the moving piece by clearing its source cell."""
        board = game_state.board
        from_y, from_x = move.from_pos.y, move.from_pos.x
        current_piece = move.piece
        if current_piece is not None:
            grid_piece = board.grid[from_y][from_x]
            if grid_piece is not None and grid_piece.color == current_piece.color and (
                grid_piece.kind == current_piece.kind or (grid_piece.kind == PieceType.PAWN and current_piece.kind == PieceType.QUEEN)
            ):
                board.grid[from_y][from_x] = None

    def execute_move_on_board(self, game_state: GameState, move: PendingMove) -> None:
        """Moves the piece on the board from from_pos to to_pos."""
        board = game_state.board
        board.move_piece(move.from_pos, move.to_pos, move.piece)

    def _handle_moving_piece_captured(self, game_state: GameState, move: PendingMove) -> Optional[Color]:
        """Handles capture of the moving piece (mid-move collision or airborne enemy)."""
        self.execute_capture(game_state, move)
        if move.piece is not None:
            move.piece.status = PieceStatus.IDLE

        if move.piece is not None and move.piece.kind == PieceType.KING:
            return Color.WHITE if move.piece.color == Color.BLACK else Color.BLACK
        return None

    def _handle_moving_piece_arrival(self, game_state: GameState, move: PendingMove) -> Optional[Color]:
        """Handles successful arrival of the moving piece at destination."""
        board = game_state.board
        
        winner_color = check_game_over(game_state, move.to_pos)

        self.promotion_service.apply_pawn_promotion(game_state, move)
        self.execute_move_on_board(game_state, move)

        if move.piece is not None:
            move.piece.cooldown_until = move.arrival + COOLDOWN_MOVE
            move.piece.status = PieceStatus.IDLE

        return winner_color

    def process_move(self, game_state: GameState, move: PendingMove) -> Optional[Color]:
        """Processes a single pending move check for captures, promotion, and movement. Returns winning Color or None."""
        if move.is_captured or self.is_captured_by_airborne_enemy(game_state, move):
            return self._handle_moving_piece_captured(game_state, move)
        else:
            return self._handle_moving_piece_arrival(game_state, move)

    def treat_pending_moves(self, game_state: GameState) -> None:
        """Finds and applies pending moves that have completed based on the current clock."""
        game_state.pending_moves.sort(key=lambda m: m.arrival)
        remaining = []
        winner_color = None
        for move in game_state.pending_moves:
            if move.arrival <= game_state.clock:
                win = self.process_move(game_state, move)
                if win is not None:
                    winner_color = win
            else:
                remaining.append(move)
        game_state.pending_moves = remaining
        if winner_color is not None:
            game_state.game_over = True

    def tick(self, game_state: GameState, ms: int) -> None:
        """Updates clock, processes pending moves, and checks game-over status."""
        self.advance_clock(game_state, ms)
        self.treat_pending_moves(game_state)
