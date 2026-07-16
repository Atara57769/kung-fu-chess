import pytest
from models.cell import Cell
from models.game_snapshot import GameSnapshot, BoardSnapshot, PendingMoveSnapshot, PieceSnapshot
from ui.history.history_tracker import UIHistoryTracker

def test_history_tracker_empty_init():
    tracker = UIHistoryTracker()
    assert len(tracker.history) == 0
    assert len(tracker.tracked_moves) == 0

def test_history_tracker_add_pending():
    tracker = UIHistoryTracker()
    
    # Create mock BoardSnapshot (width 8, height 8)
    grid = tuple(tuple(None for _ in range(8)) for _ in range(8))
    board_snap = BoardSnapshot(grid=grid, width=8, height=8)
    
    piece_snap = PieceSnapshot(color='w', kind='N', cell=Cell(7, 1))
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(7, 1),
        to_pos=Cell(5, 2),
        piece=piece_snap,
        arrival=1000,
        is_captured=False,
        path=(Cell(7, 1), Cell(5, 2))
    )
    
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=500,
        pending_moves=(move_snap,),
        jumps=()
    )
    
    tracker.update(snapshot)
    
    # Should track the move, but history should be empty (since it's still pending)
    assert len(tracker.history) == 0
    assert len(tracker.tracked_moves) == 1
    key = (7, 1, 5, 2, 'w', 'N', 1000)
    assert key in tracker.tracked_moves

def test_history_tracker_completed_move():
    tracker = UIHistoryTracker()
    
    # 1. Start with pending move
    grid = [[None for _ in range(8)] for _ in range(8)]
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)
    
    piece_snap = PieceSnapshot(color='w', kind='N', cell=Cell(7, 1))
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(7, 1),
        to_pos=Cell(5, 2),
        piece=piece_snap,
        arrival=1000,
        is_captured=False,
        path=(Cell(7, 1), Cell(5, 2))
    )
    
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=500,
        pending_moves=(move_snap,),
        jumps=()
    )
    
    tracker.update(snapshot)
    
    # 2. Complete the move (disappears from pending_moves, piece is at target)
    grid_after = [[None for _ in range(8)] for _ in range(8)]
    grid_after[5][2] = PieceSnapshot(color='w', kind='N', cell=Cell(5, 2))
    board_snap_after = BoardSnapshot(grid=tuple(tuple(r) for r in grid_after), width=8, height=8)
    
    snapshot_after = GameSnapshot(
        board=board_snap_after,
        selected_piece=None,
        game_over=False,
        clock=1000,
        pending_moves=(),
        jumps=()
    )
    
    tracker.update(snapshot_after)
    
    # Should record the move
    assert len(tracker.history) == 1
    assert len(tracker.tracked_moves) == 0
    record = tracker.history[0]
    assert record['time'] == 1000
    assert record['color'] == 'w'
    assert record['kind'] == 'N'
    assert record['to_pos'] == Cell(5, 2)

def test_history_tracker_captured_move():
    tracker = UIHistoryTracker()
    
    # 1. Start with pending move
    grid = [[None for _ in range(8)] for _ in range(8)]
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)
    
    piece_snap = PieceSnapshot(color='w', kind='N', cell=Cell(7, 1))
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(7, 1),
        to_pos=Cell(5, 2),
        piece=piece_snap,
        arrival=1000,
        is_captured=False,
        path=(Cell(7, 1), Cell(5, 2))
    )
    
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=500,
        pending_moves=(move_snap,),
        jumps=()
    )
    
    tracker.update(snapshot)
    
    # 2. Move disappears but piece is NOT at target cell (e.g. captured)
    board_snap_after = BoardSnapshot(grid=board_snap.grid, width=8, height=8) # grid is empty
    snapshot_after = GameSnapshot(
        board=board_snap_after,
        selected_piece=None,
        game_over=False,
        clock=1000,
        pending_moves=(),
        jumps=()
    )
    
    tracker.update(snapshot_after)
    
    # Should NOT record in history
    assert len(tracker.history) == 0
    assert len(tracker.tracked_moves) == 0

def test_history_tracker_promotion():
    tracker = UIHistoryTracker()
    
    # 1. Start with pending pawn move to end rank (y=0)
    grid = [[None for _ in range(8)] for _ in range(8)]
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)
    
    pawn_snap = PieceSnapshot(color='w', kind='P', cell=Cell(1, 4))
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(1, 4),
        to_pos=Cell(0, 4),
        piece=pawn_snap,
        arrival=1000,
        is_captured=False,
        path=(Cell(1, 4), Cell(0, 4))
    )
    
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=500,
        pending_moves=(move_snap,),
        jumps=()
    )
    
    tracker.update(snapshot)
    
    # 2. Complete move - pawn is promoted to Queen ('Q') at target cell
    grid_after = [[None for _ in range(8)] for _ in range(8)]
    grid_after[0][4] = PieceSnapshot(color='w', kind='Q', cell=Cell(0, 4))
    board_snap_after = BoardSnapshot(grid=tuple(tuple(r) for r in grid_after), width=8, height=8)
    
    snapshot_after = GameSnapshot(
        board=board_snap_after,
        selected_piece=None,
        game_over=False,
        clock=1000,
        pending_moves=(),
        jumps=()
    )
    
    tracker.update(snapshot_after)
    
    # Should successfully record the move (even though kind changed P -> Q)
    assert len(tracker.history) == 1
    record = tracker.history[0]
    assert record['color'] == 'w'
    assert record['kind'] == 'P'
    assert record['to_pos'] == Cell(0, 4)
