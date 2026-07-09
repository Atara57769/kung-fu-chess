from typing import Tuple, List
from constants import EMPTY_TOKEN
from models.cell import Cell
from models.pending_move import PendingMove
from models.pieces import Piece

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

    def schedule_move(self, from_pos: Cell, to_pos: Cell, piece: Piece, duration: int) -> None:
        arrival = self.clock + duration
        self.pending_moves.append(PendingMove(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=piece,
            arrival=arrival
        ))

    def advance_clock(self, ms: int) -> None:
        self.clock += ms
    
    def check_game_over(self, target_cell: Cell) -> bool:
        """Checks if the destination cell contains an enemy king, returning True if so."""
        dest_piece = self.board.get_piece_at(target_cell.y, target_cell.x)
        return dest_piece is not None and dest_piece.kind == "K"


    def execute_move(self, move: PendingMove, is_captured: bool) -> bool:
        """
        Executes a move on the board grid.
        Returns True if a game over condition is detected during execution.
        """
        from_y, from_x = move.from_pos.y, move.from_pos.x
        to_y, to_x = move.to_pos.y, move.to_pos.x

        piece_token = EMPTY_TOKEN
        if move.piece:
            piece_token = move.piece.color + move.piece.kind

        if is_captured:
            # Arriving piece is captured/removed. Only clear its source cell.
            if self.board.grid[from_y][from_x] == piece_token:
                self.board.grid[from_y][from_x] = EMPTY_TOKEN
            return False

        is_game_over = self.check_game_over(move.to_pos)
        
        # Apply the move on the grid (pawn promotion handled here)
        token = EMPTY_TOKEN
        if move.piece:
            color = move.piece.color
            kind = move.piece.kind
            if kind == "P":
                is_white_promotion = (color == "w" and to_y == 0)
                is_black_promotion = (color == "b" and to_y == self.board.height - 1)
                if is_white_promotion or is_black_promotion:
                    kind = "Q"
            token = color + kind
            move.piece.cell = move.to_pos

        self.board.grid[to_y][to_x] = token
        if self.board.grid[from_y][from_x] == piece_token:
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
                target_cell=(move.to_pos.y, move.to_pos.x),
                arrival_time=move.arrival,
                piece=move.piece
            )
            is_game_over = self.execute_move(move, is_captured)
            if is_game_over:
                game_over_detected = True
                
        self.pending_moves = remaining_moves
        return game_over_detected

    
    
    
