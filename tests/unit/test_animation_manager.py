import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui", "py")))

import pytest
from unittest.mock import MagicMock, patch
from models.cell import Cell
from models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
from ui.py.animation_manager import AnimationManager

def test_gather_active_piece_snapshots():
    # Setup mock snapshots on grid
    p1 = PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    p2 = PieceSnapshot(color="b", kind="K", cell=Cell(1, 1))
    
    mock_board = MagicMock()
    mock_board.grid = [
        [p1, None],
        [None, p2]
    ]
    
    mock_snapshot = MagicMock(spec=GameSnapshot)
    mock_snapshot.board = mock_board

    manager = AnimationManager(geometry=MagicMock(), asset_loader=MagicMock())
    snapshots = manager._gather_active_piece_snapshots(mock_snapshot)
    
    assert len(snapshots) == 2
    assert p1 in snapshots
    assert p2 in snapshots

def test_find_matching_snapshot():
    manager = AnimationManager(geometry=MagicMock(), asset_loader=MagicMock())
    
    # 1. Exact match test
    view1 = MagicMock()
    view1.color = "w"
    view1.kind = "P"
    view1.cell = Cell(0, 0)
    
    snap_exact = PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    snap_different_cell = PieceSnapshot(color="w", kind="P", cell=Cell(0, 1))
    
    match = manager._find_matching_snapshot(view1, [snap_different_cell, snap_exact])
    assert match == snap_exact

    # 2. Target cell match test (piece in transit)
    view2 = MagicMock()
    view2.color = "b"
    view2.kind = "K"
    view2.cell = Cell(0, 0)
    view2.target_cell = Cell(1, 1) # view has target_cell
    
    snap_target = PieceSnapshot(color="b", kind="K", cell=Cell(1, 1))
    
    match_target = manager._find_matching_snapshot(view2, [snap_target])
    assert match_target == snap_target

    # 3. No match test
    snap_mismatch = PieceSnapshot(color="w", kind="K", cell=Cell(1, 1))
    assert manager._find_matching_snapshot(view2, [snap_mismatch]) is None

@patch("ui.py.animation_manager.PieceView")
def test_sync_pieces_lifecycle(mock_piece_view_cls):
    # Setup mocks
    mock_geometry = MagicMock()
    mock_asset_loader = MagicMock()
    
    manager = AnimationManager(geometry=mock_geometry, asset_loader=mock_asset_loader)
    
    # Initial state: 1 active piece view (wP at Cell(0,0))
    existing_view = MagicMock()
    existing_view.color = "w"
    existing_view.kind = "P"
    existing_view.cell = Cell(0, 0)
    existing_view.target_cell = Cell(0, 1)
    manager.active_views = [existing_view]

    # Snapshots:
    # 1. The wP moved to Cell(0, 1)
    # 2. A new bK spawned at Cell(2, 2)
    p_white_moved = PieceSnapshot(color="w", kind="P", cell=Cell(0, 1))
    p_black_new = PieceSnapshot(color="b", kind="K", cell=Cell(2, 2))
    
    mock_board = MagicMock()
    mock_board.grid = [
        [p_white_moved, None],
        [None, p_black_new]
    ]
    mock_snapshot = MagicMock(spec=GameSnapshot)
    mock_snapshot.board = mock_board

    # Run sync
    manager.sync_pieces(mock_snapshot)

    # 1. Existing view must be preserved and cell updated to (0, 1)
    assert existing_view.cell == Cell(0, 1)
    assert existing_view in manager.active_views

    # 2. A new PieceView must be created for the new black king
    mock_piece_view_cls.assert_called_once_with(
        color="b",
        kind="K",
        cell=Cell(2, 2),
        geometry=mock_geometry,
        asset_loader=mock_asset_loader,
        snapshot=mock_snapshot
    )
    assert len(manager.active_views) == 2
