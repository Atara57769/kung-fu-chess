import sys
from typing import Tuple, List, Optional, Callable
from models.pieces import Piece
from services.move_scheduler import MoveScheduler
from models.cell import Cell
from models.pending_move import PendingMove
from services.move_validation_service import MoveValidationService
from services.jump_service import JumpService
from models.jump import Jump
from constants import CELL_SIZE, DURATION
from input.board_mappr import BoardMapper
from models.game_state import GameState


class boardService:
    def __init__(
        self,
        state: GameState,
        stdout,
        move_scheduler: MoveScheduler,
        move_validation_service: MoveValidationService,
        jump_service: JumpService,
        board_mapper: Optional[BoardMapper] = None,
    ):
        self.state = state
        self.board = state.board
        self.stdout = stdout
        self.move_scheduler = move_scheduler
        self.move_validation_service = move_validation_service
        self.jump_service = jump_service
        self.board_mapper = board_mapper or BoardMapper(self.board)

    @property
    def selected_piece(self) -> Optional[Piece]:
        return self.state.selected_piece

    @selected_piece.setter
    def selected_piece(self, val: Optional[Piece]) -> None:
        self.state.selected_piece = val

    @property
    def game_over(self) -> bool:
        return self.state.game_over

    @game_over.setter
    def game_over(self, val: bool) -> None:
        self.state.game_over = val


    def click(self, x: int, y: int) -> None:

        if self.game_over:
            return

        cell = self.board_mapper.pixel_to_cell(x, y)
        if cell is None:
            return
        cell_y, cell_x = cell.y, cell.x

        piece = self.board.get_piece_at(cell_y, cell_x)

        if self.selected_piece is None:
            if piece is not None:
                if not self.move_validation_service.is_piece_moving(cell_y, cell_x):
                    self.selected_piece = piece
            return

        sel_piece = self.selected_piece
        sel_y, sel_x = sel_piece.cell.y, sel_piece.cell.x
        
        if piece is not None and piece.color == sel_piece.color:
            if not self.move_validation_service.is_piece_moving(cell_y, cell_x):
                self.selected_piece = piece
            return

        if self.move_validation_service.validate_move(sel_y, sel_x, cell_y, cell_x):
            piece_to_move = self.board.get_piece_at(sel_y, sel_x)
            self.move_scheduler.schedule_move(Cell(sel_y, sel_x), Cell(cell_y, cell_x), piece_to_move, DURATION)
            self.selected_piece = None

    def jump(self, x: int, y: int) -> None:
        
        if self.game_over:
            return

        cell = self.board_mapper.pixel_to_cell(x, y)
        if cell is None:
            return
        cell_y, cell_x = cell.y, cell.x

        if self.move_validation_service.validate_jump(cell_y, cell_x):
            piece = self.board.get_piece_at(cell_y, cell_x)
            self.jump_service.schedule_jump(
                cell=(cell_y, cell_x),
                start_time=self.move_scheduler.get_clock(),
                piece=piece
            )

    def wait(self, ms: int) -> None:
        self.move_scheduler.advance_clock(ms)
        if self.move_scheduler.apply_completed_moves():
            self.game_over = True

    def print_board(self) -> None:
        """Prints the board in canonical space-separated format."""
        from output.board_printer import print_board
        print_board(self.board, stdout=self.stdout)
