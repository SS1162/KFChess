from typing import Optional

from models import BoardPosition


def pixel_to_board(x: int, y: int, cell_size: int, rows: int, cols: int) -> Optional[BoardPosition]:
    """Convert pixel coordinates to BoardPosition. Returns None if out of bounds."""
    row, col = y // cell_size, x // cell_size
    if 0 <= row < rows and 0 <= col < cols:
        return BoardPosition(row, col)
    return None
