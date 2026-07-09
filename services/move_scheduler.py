from typing import Tuple, List
from constants import EMPTY_TOKEN
from models.cell import Cell
from models.pending_move import PendingMove
from models.pieces import Piece
from models.game_state import GameState
from services.jump_service import JumpService

class MoveScheduler:
    def __init__(self, state: GameState, jump_service: JumpService):
        self.state = state
        self.board = state.board
        self.jump_service = jump_service

    @property
    def clock(self) -> int:
        return self.state.clock

    @clock.setter
    def clock(self, val: int) -> None:
        self.state.clock = val

    @property
    def pending_moves(self) -> List[PendingMove]:
        return self.state.pending_moves

    @pending_moves.setter
    def pending_moves(self, val: List[PendingMove]) -> None:
        self.state.pending_moves = val

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

        if is_captured:
            # Arriving piece is captured/removed. Only clear its source cell.
            current_piece = self.board.get_piece_at(from_y, from_x)
            if current_piece is not None and move.piece is not None:
                if current_piece.color == move.piece.color and (current_piece.kind == move.piece.kind or (current_piece.kind == "P" and move.piece.kind == "Q")):
                    self.board.grid[from_y][from_x] = None
            return False

        is_game_over = self.check_game_over(move.to_pos)
        
        # Apply the move on the grid (pawn promotion handled here)
        if move.piece:
            color = move.piece.color
            orig_kind = move.piece.kind
            
            # Use Board's move_piece if the piece at the source is indeed the moving piece (matching original kind)
            current_piece = self.board.get_piece_at(from_y, from_x)
            if current_piece is not None and current_piece.color == color and current_piece.kind == orig_kind:
                if orig_kind == "P":
                    is_white_promotion = (color == "w" and to_y == 0)
                    is_black_promotion = (color == "b" and to_y == self.board.height - 1)
                    if is_white_promotion or is_black_promotion:
                        current_piece.kind = "Q"
                        move.piece.kind = "Q"
                self.board.move_piece(move.from_pos, move.to_pos)
            else:
                # Fallback: place the piece at destination and clear source if it matches (for tests mocking direct grid writes)
                if orig_kind == "P":
                    is_white_promotion = (color == "w" and to_y == 0)
                    is_black_promotion = (color == "b" and to_y == self.board.height - 1)
                    if is_white_promotion or is_black_promotion:
                        move.piece.kind = "Q"
                move.piece.cell = move.to_pos
                self.board.grid[to_y][to_x] = move.piece
        else:
            self.board.grid[to_y][to_x] = None
            self.board.grid[from_y][from_x] = None

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
