import pytest
from models.cell import Cell
from models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
from network.protocol import (
    cell_to_algebraic, algebraic_to_cell,
    move_to_algebraic, algebraic_to_move,
    serialize_snapshot, deserialize_snapshot
)

def test_algebraic_cell_conversions():
    """Verify Cell objects convert to and from algebraic notation correctly."""
    # 8x8 Board
    # Cell(y=7, x=4) -> e1
    cell = Cell(y=7, x=4)
    assert cell_to_algebraic(cell, 8) == "e1"
    assert algebraic_to_cell("e1", 8) == cell

    # Cell(y=0, x=0) -> a8
    cell2 = Cell(y=0, x=0)
    assert cell_to_algebraic(cell2, 8) == "a8"
    assert algebraic_to_cell("a8", 8) == cell2

    # Custom board height: 10
    # Cell(y=0, x=1) -> b10
    cell3 = Cell(y=0, x=1)
    assert cell_to_algebraic(cell3, 10) == "b10"
    assert algebraic_to_cell("b10", 10) == cell3

def test_algebraic_move_conversions():
    """Verify moves convert to and from algebraic notation correctly."""
    from_cell, to_cell = algebraic_to_move("e2e4", 8)
    assert from_cell == Cell(y=6, x=4)
    assert to_cell == Cell(y=4, x=4)
    assert move_to_algebraic(from_cell, to_cell, 8) == "e2e4"

    # Multi-digit rank
    from_cell2, to_cell2 = algebraic_to_move("b10b12", 12)
    assert from_cell2 == Cell(y=2, x=1)
    assert to_cell2 == Cell(y=0, x=1)
    assert move_to_algebraic(from_cell2, to_cell2, 12) == "b10b12"

def test_snapshot_serialization():
    """Verify GameSnapshot objects serialize and deserialize correctly."""
    piece = PieceSnapshot(color="w", kind="K", cell=Cell(y=0, x=0), cooldown_until=0, status="IDLE")
    grid = ((piece, None), (None, None))
    board = BoardSnapshot(grid=grid, width=2, height=2)
    
    snapshot = GameSnapshot(
        board=board,
        selected_piece=piece,
        game_over=False,
        clock=100,
        pending_moves=(),
        jumps=()
    )
    
    serialized = serialize_snapshot(snapshot)
    deserialized = deserialize_snapshot(serialized)
    
    assert deserialized.clock == snapshot.clock
    assert deserialized.game_over == snapshot.game_over
    assert deserialized.board.width == snapshot.board.width
    assert deserialized.board.height == snapshot.board.height
    assert deserialized.selected_piece.color == "w"
    assert deserialized.selected_piece.kind == "K"
    assert deserialized.board.grid[0][0].color == "w"
    assert deserialized.board.grid[0][1] is None
