from services.move_scheduler import PendingMove
from services.game_over_service import GameOverService
from constants import EMPTY_TOKEN

class MoveExecutionService:
    def __init__(self, board, game_over_service: GameOverService):
        self.board = board
        self.game_over_service = game_over_service

    def execute_move(self, move: PendingMove, is_captured: bool) -> bool:
        """
        Executes a move on the board grid.
        Returns True if a game over condition is detected during execution.
        """
        from_y, from_x = move.from_pos
        to_y, to_x = move.to_pos

        if is_captured:
            # Arriving piece is captured/removed. Only clear its source cell.
            if self.board.grid[from_y][from_x] == move.piece.token:
                self.board.grid[from_y][from_x] = EMPTY_TOKEN
            return False

        is_game_over = self.game_over_service.check_game_over(move.to_pos)
        
        # Apply the move on the grid (piece-owned promotion called here)
        token = move.piece.promote(to_y, len(self.board.grid)) if move.piece else EMPTY_TOKEN
        self.board.grid[to_y][to_x] = token
        if self.board.grid[from_y][from_x] == move.piece.token:
            self.board.grid[from_y][from_x] = EMPTY_TOKEN

        return is_game_over
