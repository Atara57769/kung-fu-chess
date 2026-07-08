from dataclasses import dataclass
from typing import Tuple, List
from models.pieces import Piece
from constants import EMPTY_TOKEN


@dataclass
class PendingMove:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    piece: Piece
    arrival: int

class MoveScheduler:
    def __init__(self, board ,jump_service):
        self.board = board
        self.jump_service = jump_service
        self.clock: int = 0
        self.pending_moves: List[PendingMove] = []

    def get_clock(self) -> int:
        return self.clock

    def get_pending_moves(self) -> List[PendingMove]:
        return self.pending_moves

    def schedule_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], piece: Piece, duration: int) -> None:
        arrival = self.clock + duration
        self.pending_moves.append(PendingMove(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=piece,
            arrival=arrival
        ))

    def advance_clock(self, ms: int) -> None:
        self.clock += ms
    
    def check_game_over(self, target_cell: Tuple[int, int]) -> bool:
        """Checks if the destination cell contains an enemy king, returning True if so."""
        dest_y, dest_x = target_cell
        dest_piece = self.board.get_piece_at(dest_y, dest_x)
        return dest_piece is not None and dest_piece.is_king


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

        is_game_over = self.check_game_over(move.to_pos)
        
        # Apply the move on the grid (piece-owned promotion called here)
        token = move.piece.promote(to_y, len(self.board.grid)) if move.piece else EMPTY_TOKEN
        self.board.grid[to_y][to_x] = token
        if self.board.grid[from_y][from_x] == move.piece.token:
            self.board.grid[from_y][from_x] = EMPTY_TOKEN

        return is_game_over

    def apply_completed_moves(self) -> bool:
        """
        Sorts pending moves and applies all moves whose arrival time has passed.
        Returns True if a game over condition is detected during execution.
        """
        self.pending_moves.sort(key=lambda move: move.arrival)
        
        game_over_detected = False
        remaining_moves = []
        for move in self.pending_moves:
            if move.arrival > self.clock:
                remaining_moves.append(move)
                continue
            
            is_captured = self.jump_service.is_captured_by_airborne_enemy(
                target_cell=move.to_pos,
                arrival_time=move.arrival,
                piece=move.piece
            )
            is_game_over = self.execute_move(move, is_captured)
            if is_game_over:
                game_over_detected = True
                
        self.pending_moves = remaining_moves
        return game_over_detected
    
    
    
