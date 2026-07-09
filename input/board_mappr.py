from models.cell import Cell
from constants import CELL_SIZE

class BoardMapper:
    def __init__(self, board):
        self.board = board

    def pixel_to_cell(self, x: int, y: int) -> Cell | None:
        if x < 0 or y < 0:
            return None
        cell_y = y // CELL_SIZE
        cell_x = x // CELL_SIZE
        if 0 <= cell_x < self.board.width and 0 <= cell_y < self.board.height:
            return Cell(cell_y, cell_x)
        return None