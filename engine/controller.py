from typing import Optional
from models.game_state import GameState
from models.cell import Cell
from engine.game_engine import GameEngine
from input.board_mappr import BoardMapper


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

    def click(self, x: int, y: int) -> None:
        if self.state.game_over:
            return

        cell = self.board_mapper.pixel_to_cell(x, y)

        # Out of board
        if cell is None:
            # Cancel any existing selection if the click was outside the board
            self.state.selected_piece = None
            return

        board = self.state.board
        piece = board.get_piece_at(cell)

        # --- No piece selected yet ---
        if self.state.selected_piece is None:
            if piece is None:
                return  # empty cell, nothing to select
            # Only select if not already in transit
            if not self.game_engine.is_piece_moving(self.state, cell):
                self.state.selected_piece = piece
            return

        # --- Piece already selected ---
        sel_piece = self.state.selected_piece
        sel_cell = sel_piece.cell

        # Clicking a friendly piece → re-select (if not moving)
        if piece is not None and piece.color == sel_piece.color:
            if not self.game_engine.is_piece_moving(self.state, cell):
                self.state.selected_piece = piece
            return

        # Second click → try to move
        self.game_engine.request_move(self.state, sel_cell, cell)
        self.state.selected_piece = None

    def wait(self, ms: int) -> None:
        self.game_engine.wait(self.state, ms)

    def jump(self, x: int, y: int) -> None:
        if self.state.game_over:
            return

        cell = self.board_mapper.pixel_to_cell(x, y)
        if cell is None:
            return

        board = self.state.board
        piece = board.get_piece_at(cell)
        if piece is None:
            return

        self.game_engine.jump(self.state, cell)

    def print_board(self) -> None:
        self.game_engine.print_board(self.state, self.stdout)
