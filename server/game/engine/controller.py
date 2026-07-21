import logging
from typing import Optional
from shared.models.game_state import GameState
from shared.models.cell import Cell
from server.game.engine.game_engine import GameEngine
from shared.models.game_snapshot import GameSnapshot

logger = logging.getLogger(__name__)


from shared.models.color import Color

class Controller:
    """
    Thin input layer: translates pixel coordinates and events into
    GameEngine calls. Manages piece selection in game_state.
    """

    def __init__(self, state: GameState, game_engine: GameEngine, stdout):
        self.state = state
        self.game_engine = game_engine
        self.stdout = stdout

    def _get_selection(self, player_color: Optional[Color]) -> Optional[any]:
        if player_color == Color.BLACK:
            return self.state.black_selected_piece
        else:
            return self.state.selected_piece

    def _set_selection(self, player_color: Optional[Color], piece: Optional[any]) -> None:
        if player_color == Color.BLACK:
            self.state.black_selected_piece = piece
        else:
            self.state.selected_piece = piece

    def get_snapshot(self, player_color: Optional[Color] = None) -> GameSnapshot:
        """Returns a snapshot of the current game state, with selected_piece matching player_color selection."""
        old_selected = self.state.selected_piece
        self.state.selected_piece = self._get_selection(player_color)
        snap = self.game_engine.snapshot(self.state)
        self.state.selected_piece = old_selected
        return snap

    def click(self, cell: Optional[Cell], player_color: Optional[Color] = None) -> None:
        if self.state.game_over:
            return

        if cell is not None and not self.state.board.is_inside_bounds(cell.y, cell.x):
            cell = None

        if cell is None:
            self._set_selection(player_color, None)
            return

        self._check_selected_piece_killed(player_color)

        current_selection = self._get_selection(player_color)
        if current_selection is None:
            self._handle_no_selection_state(cell, player_color)
        else:
            self._handle_selected_state(cell, player_color)

    def _check_selected_piece_killed(self, player_color: Optional[Color]) -> None:
        """Resets the selection if the selected piece was killed/captured."""
        sel_piece = self._get_selection(player_color)
        if sel_piece is not None:
            if sel_piece.cell is None or self.state.board.get_piece_at(sel_piece.cell) is not sel_piece:
                self._set_selection(player_color, None)

    def _handle_no_selection_state(self, cell: Cell, player_color: Optional[Color]) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            return
        
        if player_color is not None and piece.color != player_color:
            return

        if not self.game_engine.is_piece_moving(self.state, cell):
            self._set_selection(player_color, piece)

    def _handle_selected_state(self, cell: Cell, player_color: Optional[Color]) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        sel_piece = self._get_selection(player_color)
        if sel_piece is None:
            return
        
        sel_cell = sel_piece.cell

        if piece is not None and piece.color == sel_piece.color:
            if not self.game_engine.is_piece_moving(self.state, cell):
                self._set_selection(player_color, piece)
                return

        if not self.game_engine.is_piece_moving(self.state, sel_cell):
            self.game_engine.request_move(self.state, sel_cell, cell)
        self._set_selection(player_color, None)

    def wait(self, ms: int) -> None:
        self.game_engine.wait(self.state, ms)

    def jump(self, cell: Optional[Cell], player_color: Optional[Color] = None) -> None:
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

        if player_color is not None and piece.color != player_color:
            logger.warning(f"Unauthorized jump click at {cell} by player {player_color}")
            return

        self.game_engine.jump(self.state, cell)

    def print_board(self) -> None:
        self.game_engine.print_board(self.state, self.stdout)
