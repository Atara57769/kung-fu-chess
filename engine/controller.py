import logging
from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from engine.game_engine import GameEngine
from input.board_mappr import BoardMapper

logger = logging.getLogger(__name__)


class Controller:
    """
    Thin input layer: translates pixel coordinates and events into
    GameEngine calls. Manages piece selection in game_state.
    """

    def __init__(self, state: GameState, game_engine: GameEngine, stdout,
                 board_mapper: Optional[BoardMapper] = None):
        self.state = state
        self.game_engine = game_engine
        self.stdout = stdout
        self.board_mapper = board_mapper or BoardMapper(state.board)
        logger.debug("Controller initialized.")

    def click(self, x: int, y: int) -> None:
        if self.state.game_over:
            logger.info("Ignoring click: game is over.")
            return

        cell = self.board_mapper.pixel_to_cell(x, y)
        logger.debug(f"Click at ({x}, {y}) resolved to cell: {cell}")

        # Out of board
        if cell is None:
            # Cancel any existing selection if the click was outside the board
            logger.info("Click outside board. Cancelling selection.")
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
                logger.info(f"Selected piece {sel_piece} was killed before second click. Resetting selection.")
                self.state.selected_piece = None

    def _handle_no_selection_state(self, cell: Cell) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            logger.debug(f"Click on empty cell {cell}; no piece selected.")
            return  # empty cell, nothing to select
        # Only select if not already in transit
        if not self.game_engine.is_piece_moving(self.state, cell):
            logger.info(f"Selecting piece: {piece} at {cell}")
            self.state.selected_piece = piece
        else:
            logger.info(f"Cannot select moving piece: {piece} at {cell}")

    def _handle_selected_state(self, cell: Cell) -> None:
        board = self.state.board
        piece = board.get_piece_at(cell)
        sel_piece = self.state.selected_piece
        
        sel_cell = sel_piece.cell

        # Clicking a friendly piece → re-select (if not moving)
        if piece is not None and piece.color == sel_piece.color:
            if not self.game_engine.is_piece_moving(self.state, cell):
                logger.info(f"Re-selecting friendly piece: {piece} at {cell}")
                self.state.selected_piece = piece
            else:
                logger.info(f"Cannot re-select moving friendly piece: {piece} at {cell}")
            return

        # Second click → try to move
        logger.info(f"Requesting move from {sel_cell} to {cell}")
        self.game_engine.request_move(self.state, sel_cell, cell)
        self.state.selected_piece = None

    def wait(self, ms: int) -> None:
        logger.debug(f"Waiting for {ms} ms")
        self.game_engine.wait(self.state, ms)

    def jump(self, x: int, y: int) -> None:
        if self.state.game_over:
            logger.info("Ignoring jump: game is over.")
            return

        cell = self.board_mapper.pixel_to_cell(x, y)
        logger.debug(f"Jump click at ({x}, {y}) resolved to cell: {cell}")
        if cell is None:
            logger.warning(f"Jump click ({x}, {y}) was out of bounds.")
            return

        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            logger.warning(f"Jump click at {cell} has no piece to jump.")
            return

        logger.info(f"Requesting jump for piece {piece} at {cell}")
        self.game_engine.jump(self.state, cell)

    def print_board(self) -> None:
        logger.debug("Printing board layout.")
        self.game_engine.print_board(self.state, self.stdout)
