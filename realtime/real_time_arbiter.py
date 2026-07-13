import logging
from models.game_state import GameState
from models.pending_move import PendingMove
from models.cell import Cell
from constants import COLOR_WHITE, COLOR_BLACK, PIECE_KING, PIECE_QUEEN, PIECE_PAWN,COOLDOWN_DURATION

from rules.win_condition import check_game_over
from rules.promotion import PawnPromotion

logger = logging.getLogger(__name__)


class RealTimeArbiter:
    def __init__(self, promotion_service=None) -> None:
        self.promotion_service = promotion_service or PawnPromotion()
        logger.debug("RealTimeArbiter initialized.")

    def advance_clock(self, game_state: GameState, ms: int) -> None:
        """Advances the clock of the game state by the given milliseconds."""
        game_state.clock += ms
        logger.debug(f"Clock advanced by {ms} ms. Current clock: {game_state.clock}")

    def is_captured_by_airborne_enemy(self, game_state: GameState, move: PendingMove) -> bool:
        """Checks if the destination cell contains an active airborne enemy piece."""
        to_y, to_x = move.to_pos.y, move.to_pos.x
        for jump in game_state.jumps:
            if jump.cell == (to_y, to_x) and jump.start <= move.arrival <= jump.end:
                if jump.piece.color != move.piece.color:
                    logger.info(f"Move destination {move.to_pos} occupied by airborne enemy: {jump.piece}")
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
                grid_piece.kind == current_piece.kind or (grid_piece.kind == PIECE_PAWN and current_piece.kind == PIECE_QUEEN)
            ):
                logger.info(f"Piece {current_piece} captured. Clearing source cell {move.from_pos}.")
                board.grid[from_y][from_x] = None

    def execute_move_on_board(self, game_state: GameState, move: PendingMove) -> None:
        """Moves the piece on the board from from_pos to to_pos."""
        board = game_state.board
        logger.info(f"Moving piece {move.piece} from {move.from_pos} to {move.to_pos} on board grid.")
        board.move_piece(move.from_pos, move.to_pos, move.piece)

    def process_move(self, game_state: GameState, move: PendingMove) -> bool:
        """Processes a single pending move check for captures, promotion, and movement."""
        logger.info(f"Processing completed move: {move}")
        if move.is_captured or self.is_captured_by_airborne_enemy(game_state, move):
            logger.info(f"Move from {move.from_pos} to {move.to_pos} failed due to capture/collision.")
            self.execute_capture(game_state, move)
            return False

        is_game_over = check_game_over(game_state, move.to_pos)
        if is_game_over:
            logger.info(f"Game over detected after move to {move.to_pos}")

        self.promotion_service.apply_pawn_promotion(game_state, move)
        self.execute_move_on_board(game_state, move)

        if move.piece is not None:
            move.piece.cooldown_until = move.arrival + COOLDOWN_DURATION
            logger.debug(f"Set cooldown for {move.piece} until {move.piece.cooldown_until}")

        return is_game_over

    def treat_pending_moves(self, game_state: GameState) -> None:
        """Finds and applies pending moves that have completed based on the current clock."""
        game_state.pending_moves.sort(key=lambda m: m.arrival)
        remaining = []
        game_over_detected = False
        for move in game_state.pending_moves:
            if move.arrival <= game_state.clock:
                if self.process_move(game_state, move):
                    game_over_detected = True
            else:
                remaining.append(move)
        game_state.pending_moves = remaining
        if game_over_detected:
            logger.info("Setting game_over status to True.")
            game_state.game_over = True

    def tick(self, game_state: GameState, ms: int) -> None:
        """Updates clock, processes pending moves, and checks game-over status."""
        logger.debug(f"Tick: advancing by {ms} ms")
        self.advance_clock(game_state, ms)
        self.treat_pending_moves(game_state)
