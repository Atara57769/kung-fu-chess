from shared.models.cell import Cell
from shared.constants import CELL_SIZE

class BoardGeometry:
    def __init__(self, cell_size: int = CELL_SIZE):
        self.cell_size = cell_size

    def cell_to_top_left_pixel(self, cell: Cell) -> tuple[int, int]:
        """
        Returns (x, y) pixels for the top-left corner of the cell.
        """
        return cell.x * self.cell_size, cell.y * self.cell_size

    def cell_to_center_pixel(self, cell: Cell) -> tuple[int, int]:
        """
        Returns (x, y) pixels for the center of the cell.
        """
        offset = self.cell_size // 2
        return cell.x * self.cell_size + offset, cell.y * self.cell_size + offset

    def pixel_to_cell(self, px: int, py: int) -> Cell | None:
        """
        Converts screen pixel coordinates (px, py) to a Cell coordinate.
        """
        if px < 0 or py < 0:
            return None
        cell_x = px // self.cell_size
        cell_y = py // self.cell_size
        return Cell(y=cell_y, x=cell_x)
