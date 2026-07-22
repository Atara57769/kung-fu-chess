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

    def get_snapshot(self, player_color: Optional[Color] = None) -> GameSnapshot:
        """Returns a snapshot of the current game state."""
        return self.game_engine.snapshot(self.state)

    def move(self, from_cell: Optional[Cell], to_cell: Optional[Cell], player_color: Optional[Color] = None) -> None:
        if self.state.game_over:
            return

        if from_cell is None or to_cell is None:
            return

        if not self.state.board.is_inside_bounds(from_cell.y, from_cell.x) or not self.state.board.is_inside_bounds(to_cell.y, to_cell.x):
            return

        piece = self.state.board.get_piece_at(from_cell)
        if piece is None:
            return

        if player_color is not None and piece.color != player_color:
            return

        if not self.game_engine.is_piece_moving(self.state, from_cell):
            self.game_engine.request_move(self.state, from_cell, to_cell)


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
