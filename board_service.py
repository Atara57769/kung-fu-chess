from dataclasses import dataclass
from typing import Tuple, List, Optional
from models.pieces import get_piece, Piece


@dataclass
class PendingMove:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    piece: Piece
    arrival: int


@dataclass
class Jump:
    cell: Tuple[int, int]
    start: int
    end: int
    piece: Piece


class boardService:
    def __init__(self, board):
        self.board = board
        self.selected_piece: Optional[Tuple[int, int]] = None
        self.clock: int = 0
        self.pending_moves: List[PendingMove] = []
        self.game_over: bool = False
        self.jumps: List[Jump] = []

    def _is_within_bounds(self, row: int, col: int) -> bool:
        """Checks if the cell coordinates (row, col) are within the board boundaries."""
        return 0 <= col < self.board.width and 0 <= row < len(self.board.grid)

    def _is_piece_moving(self, row: int, col: int) -> bool:
        """Checks if a piece at (row, col) is currently in transit as a source of a pending move."""
        return any(move.from_pos == (row, col) for move in self.pending_moves)

    def _is_destination_reserved(self, row: int, col: int) -> bool:
        """Checks if a cell (row, col) is the target destination of any pending move."""
        return any(move.to_pos == (row, col) for move in self.pending_moves)

    def _is_captured_by_airborne_enemy(self, target_cell: Tuple[int, int], arrival_time: int, piece: Piece) -> bool:
        """Checks if the destination contains an active airborne piece of the enemy."""
        for jump in self.jumps:
            if jump.cell == target_cell and jump.start <= arrival_time <= jump.end:
                if jump.piece.color != piece.color:
                    return True
        return False

    def _check_game_over(self, target_cell: Tuple[int, int]) -> None:
        """Checks if the destination cell contains an enemy king, setting game_over to True if so."""
        dest_y, dest_x = target_cell
        dest_token = self.board.grid[dest_y][dest_x]
        dest_piece = get_piece(dest_token)
        if dest_piece is not None and dest_piece.is_king:
            self.game_over = True

    def _promote_pawn(self, piece: Piece, to_y: int) -> str:
        """Promotes a pawn to a queen if it reaches the opposite back rank."""
        if piece.is_pawn:
            is_white_promotion = (piece.color == 'w' and to_y == 0)
            is_black_promotion = (piece.color == 'b' and to_y == len(self.board.grid) - 1)
            if is_white_promotion or is_black_promotion:
                from models.pieces import Queen
                return Queen(piece.color).token
        return piece.token

    def _execute_move(self, move: PendingMove, is_captured: bool) -> None:
        """Applies or discards the move based on whether the arriving piece was captured in transit."""
        from_y, from_x = move.from_pos
        to_y, to_x = move.to_pos

        if is_captured:
            # Arriving piece is captured/removed. Only clear its source cell.
            if self.board.grid[from_y][from_x] == move.piece.token:
                self.board.grid[from_y][from_x] = '.'
            return

        self._check_game_over(move.to_pos)
        
        token = self._promote_pawn(move.piece, to_y)

        # Apply the move on the grid
        self.board.grid[to_y][to_x] = token
        if self.board.grid[from_y][from_x] == move.piece.token:
            self.board.grid[from_y][from_x] = '.'

    def _apply_completed_moves(self) -> None:
        """Sorts pending moves and applies all moves whose arrival time has passed."""
        self.pending_moves.sort(key=lambda move: move.arrival)
        
        remaining_moves = []
        for move in self.pending_moves:
            if move.arrival > self.clock:
                remaining_moves.append(move)
                continue
            
            is_captured = self._is_captured_by_airborne_enemy(
                target_cell=move.to_pos,
                arrival_time=move.arrival,
                piece=move.piece
            )
            self._execute_move(move, is_captured)
            
        self.pending_moves = remaining_moves

    def click(self, x: int, y: int) -> None:
        self._apply_completed_moves()
        if self.game_over or self.pending_moves:
            return

        cell_y = y // 100
        cell_x = x // 100

        if not self._is_within_bounds(cell_y, cell_x):
            return

        token = self.board.grid[cell_y][cell_x]

        if self._is_piece_moving(cell_y, cell_x):
            return

        # If no piece is selected, clicking a non-empty cell selects it
        if self.selected_piece is None:
            if token != '.':
                self.selected_piece = (cell_y, cell_x)
            return

        # A piece is already selected
        sel_y, sel_x = self.selected_piece
        sel_token = self.board.grid[sel_y][sel_x]
        
        piece = get_piece(token)
        sel_piece = get_piece(sel_token)

        # If clicking another friendly piece, replace the selection
        if piece is not None and sel_piece is not None and piece.color == sel_piece.color:
            if self._is_piece_moving(cell_y, cell_x):
                return
            self.selected_piece = (cell_y, cell_x)
            return

        # Check if the selected piece is already in transit
        if self._is_piece_moving(sel_y, sel_x):
            return

        # Check if the destination is targeted by another pending move
        if self._is_destination_reserved(cell_y, cell_x):
            return

        # Validate the move according to the piece type
        if sel_piece is None or sel_piece.is_legal_move(self.board, sel_y, sel_x, cell_y, cell_x):
            # Calculate travel duration
            duration = 1000
            if sel_piece is not None:
                duration = sel_piece.get_travel_duration(sel_y, sel_x, cell_y, cell_x)

            # Schedule the move
            self.pending_moves.append(PendingMove(
                from_pos=(sel_y, sel_x),
                to_pos=(cell_y, cell_x),
                piece=sel_piece,
                arrival=self.clock + duration
            ))
            self.selected_piece = None

    def jump(self, x: int, y: int) -> None:
        self._apply_completed_moves()
        if self.game_over:
            return

        cell_y = y // 100
        cell_x = x // 100

        if not self._is_within_bounds(cell_y, cell_x):
            return

        token = self.board.grid[cell_y][cell_x]
        if token == '.':
            return

        # A moving piece cannot jump (nor can a piece being captured/targeted)
        if self._is_piece_moving(cell_y, cell_x) or self._is_destination_reserved(cell_y, cell_x):
            return

        piece = get_piece(token)
        if piece is not None:
            # Schedule the jump
            self.jumps.append(Jump(
                cell=(cell_y, cell_x),
                start=self.clock,
                end=self.clock + 1000,
                piece=piece
            ))

    def wait(self, ms: int) -> None:
        self.clock += ms
        self._apply_completed_moves()

    def print_board(self) -> None:
        """Prints the board in canonical space-separated format."""
        self._apply_completed_moves()
        for row in self.board.grid:
            print(" ".join(row))
