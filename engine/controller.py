import logging
from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from engine.game_engine import GameEngine
from models.game_snapshot import GameSnapshot

logger = logging.getLogger(__name__)


class Controller:
    """
    Thin input layer: translates pixel coordinates and events into
    GameEngine calls. Manages piece selection in game_state.
    """

    def __init__(self, state: GameState, game_engine: GameEngine, stdout):
        self.state = state
        self.game_engine = game_engine
        self.stdout = stdout


    def get_snapshot(self) -> GameSnapshot:
        """Returns a snapshot of the current game state."""
        return self.game_engine.snapshot(self.state)

    def click(self, cell: Optional[Cell]) -> None:
        if self.state.game_over:
            return

        if cell is not None and not self.state.board.is_inside_bounds(cell.y, cell.x):
            cell = None

        if cell is None:
            self.state.selected_piece = None
            return

        self._check_selected_piece_killed()

        if self.state.selected_piece is None:
            self._handle_no_selection_state(cell)
        else:
            self._handle_selected_state(cell)

    def _check_selected_piece_killed(self) -> None:
        """Resets the selection if the selected piece was killed/captured."""
        if self.state.selected_piece is not None:
            sel_piece = self.state.selected_piece
            if sel_piece.cell is None or self.state.board.get_piece_at(sel_piece.cell) is not sel_piece:
                self.state.selected_piece = None

    def _handle_no_selection_state(self, cell: Cell) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            return
        if not self.game_engine.is_piece_moving(self.state, cell):
            self.state.selected_piece = piece

    def _handle_selected_state(self, cell: Cell) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        sel_piece = self.state.selected_piece
        
        sel_cell = sel_piece.cell

        if piece is not None and piece.color == sel_piece.color:
            if not self.game_engine.is_piece_moving(self.state, cell):
                self.state.selected_piece = piece
                return

        if not self.game_engine.is_piece_moving(self.state, sel_cell):
            self.game_engine.request_move(self.state, sel_cell, cell)
        self.state.selected_piece = None

    def wait(self, ms: int) -> None:
        self.game_engine.wait(self.state, ms)

    def jump(self, cell: Optional[Cell]) -> None:
        if self.state.game_over:
            return

        if cell is not None and not self.state.board.is_inside_bounds(cell.y, cell.x):
            cell = None

        if cell is None:
            logger.warning("Jump click was out of bounds.")
            return

        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            logger.warning(f"Jump click at {cell} has no piece to jump.")
            return

        self.game_engine.jump(self.state, cell)

    def print_board(self) -> None:
        self.game_engine.print_board(self.state, self.stdout)
