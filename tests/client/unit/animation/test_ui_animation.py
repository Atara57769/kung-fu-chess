import pytest
from unittest.mock import MagicMock
from shared.models.cell import Cell
from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot, PendingMoveSnapshot, JumpSnapshot
from client.ui.board.board_geometry import BoardGeometry
from client.ui.animation.piece_view import PieceView, STATE_REGISTRY
from client.ui.animation.states.animation_state import AnimationState
from client.ui.animation.states.idle_state import IdleState
from client.ui.animation.states.move_state import MoveState
from client.ui.animation.states.jump_state import JumpState
from client.ui.animation.states.short_rest_state import ShortRestState
from client.ui.animation.states.long_rest_state import LongRestState
from client.ui.rendering.img import Img

class DummyState(AnimationState):
    def update(self, dt: float, piece_view, snapshot: GameSnapshot) -> None:
        pass

def test_animation_state_base():
    # Test AnimationState base methods
    config = {"graphics": {"frames_per_sec": 10, "is_loop": True}}
    sprites = [MagicMock(spec=Img), MagicMock(spec=Img)]
    state = DummyState("dummy", config, sprites)
    
    assert state.get_sprite() == sprites[0]
    
    # advance_frames with loops
    state.advance_frames(0.05) # elapsed = 0.05. frame duration = 0.1. frame = 0
    assert state.current_frame_index == 0
    
    state.advance_frames(0.06) # elapsed = 0.11. frame = 1
    assert state.current_frame_index == 1
    
    state.advance_frames(0.1) # elapsed = 0.21. frame = 2 % 2 = 0
    assert state.current_frame_index == 0

    # test non-looping
    config_noloop = {"graphics": {"frames_per_sec": 10, "is_loop": False}}
    state_noloop = DummyState("dummy", config_noloop, sprites)
    state_noloop.advance_frames(1.0) # elapsed = 1.0. frame index = 10 -> capped at 1
    assert state_noloop.current_frame_index == 1

    # Exception when empty sprites
    state_empty = DummyState("dummy", {}, [])
    with pytest.raises(ValueError, match="No sprites loaded"):
        state_empty.get_sprite()
        
    state_empty.advance_frames(1.0) # should return silently

def test_piece_view_initialization_and_exceptions():
    geometry = BoardGeometry(cell_size=100)
    asset_loader = MagicMock()
    
    mock_assets = MagicMock()
    mock_assets.config = {}
    mock_assets.sprites = [MagicMock(spec=Img)]
    asset_loader.get_piece_assets.return_value = mock_assets
    
    snapshot = MagicMock(spec=GameSnapshot)
    
    # 1. Successful initialization
    pv = PieceView(color="w", kind="P", cell=Cell(1, 2), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot)
    assert pv.color == "w"
    assert pv.kind == "P"
    assert pv.cell == Cell(1, 2)
    assert pv.px == 200
    assert pv.py == 100
    assert pv.get_sprite() == mock_assets.sprites[0]

    # 2. Unknown state transition
    with pytest.raises(ValueError, match="Unknown animation state"):
        pv.change_state("invalid_state", snapshot)

def test_idle_state_transitions():
    geometry = BoardGeometry(cell_size=100)
    asset_loader = MagicMock()
    mock_assets = MagicMock()
    mock_assets.config = {}
    mock_assets.sprites = [MagicMock(spec=Img)]
    asset_loader.get_piece_assets.return_value = mock_assets
    
    # Create BoardSnapshot and GameSnapshot
    board_snap = BoardSnapshot(grid=((None,),), width=1, height=1)
    
    # GameSnapshot with pending move
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(0, 0), to_pos=Cell(0, 1),
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0)),
        arrival=500, is_captured=False, path=(Cell(0, 0), Cell(0, 1))
    )
    
    snapshot_move = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=0,
        pending_moves=(move_snap,), jumps=()
    )
    
    pv = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_move)
    pv.change_state("idle", snapshot_move)
    
    # update idle state with pending move -> transitions to move state
    pv.update(0.1, snapshot_move)
    assert pv.state.name == "move"

    # GameSnapshot with jump
    jump_snap = JumpSnapshot(
        cell=(0, 0), start=0, end=1000,
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    )
    snapshot_jump = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=0,
        pending_moves=(), jumps=(jump_snap,)
    )
    
    pv2 = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_jump)
    pv2.change_state("idle", snapshot_jump)
    pv2.update(0.1, snapshot_jump)
    assert pv2.state.name == "jump"

    # GameSnapshot with expired jump -> no transition
    jump_expired = JumpSnapshot(
        cell=(0, 0), start=0, end=1000,
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    )
    snapshot_expired = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=1000,
        pending_moves=(), jumps=(jump_expired,)
    )
    pv3 = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_expired)
    pv3.change_state("idle", snapshot_expired)
    pv3.update(0.1, snapshot_expired)
    assert pv3.state.name == "idle"

def test_move_state_logic():
    geometry = BoardGeometry(cell_size=100)
    asset_loader = MagicMock()
    mock_assets = MagicMock()
    mock_assets.config = {"physics": {"next_state_when_finished": "long_rest"}}
    mock_assets.sprites = [MagicMock(spec=Img)]
    asset_loader.get_piece_assets.return_value = mock_assets
    
    board_snap = BoardSnapshot(grid=((None,),), width=1, height=1)
    
    # 1. Progress interpolation with multiple path elements
    move_snap = PendingMoveSnapshot(
        from_pos=Cell(0, 0), to_pos=Cell(0, 2),
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0)),
        arrival=1000, is_captured=False, path=(Cell(0, 0), Cell(0, 1), Cell(0, 2))
    )
    snapshot = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=500,
        pending_moves=(move_snap,), jumps=()
    )
    
    pv = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot)
    pv.change_state("move", snapshot)
    
    pv.update(0.1, snapshot)
    # Clock is 500, start was 500 in snapshot. clock=500 -> progress = 0.0
    # Let's verify coordinates
    assert pv.px == 0
    assert pv.py == 0

    # Advance clock to 750 (progress = 0.5)
    # Path length = 3. scaled_progress = 0.5 * 2 = 1.0. idx = 1, seg_prog = 0.0. cell_a = path[1] (0, 1), cell_b = path[2] (0, 2)
    # Target top-left of cell (0, 1) is (100, 0).
    snapshot_mid = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=750,
        pending_moves=(move_snap,), jumps=()
    )
    pv.update(0.1, snapshot_mid)
    assert pv.px == 100
    assert pv.py == 0

    # Advance clock to 1000 (finished) -> progress = 1.0 -> transitions to long_rest and cell is updated to (0, 2)
    snapshot_end = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=1000,
        pending_moves=(move_snap,), jumps=()
    )
    pv.update(0.1, snapshot_end)
    assert pv.cell == Cell(0, 2)
    assert pv.state.name == "long_rest"

    # 2. Case where active move disappears (e.g. cancelled/completed outside) -> transition to rest state
    snapshot_empty = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=600,
        pending_moves=(), jumps=()
    )
    pv_cancel = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot)
    pv_cancel.change_state("move", snapshot)
    pv_cancel.update(0.1, snapshot_empty)
    assert pv_cancel.state.name == "long_rest"

    # 3. Path of length 1 or 0
    move_snap_short = PendingMoveSnapshot(
        from_pos=Cell(0, 0), to_pos=Cell(0, 1),
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0)),
        arrival=1000, is_captured=False, path=(Cell(0, 1),)
    )
    snapshot_short = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=500,
        pending_moves=(move_snap_short,), jumps=()
    )
    pv_short = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_short)
    pv_short.change_state("move", snapshot_short)
    pv_short.update(0.1, snapshot_short)
    assert pv_short.px == 100 # directly at to_pos

    # 4. Duration <= 0 fallback
    move_snap_instant = PendingMoveSnapshot(
        from_pos=Cell(0, 0), to_pos=Cell(0, 1),
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0)),
        arrival=500, is_captured=False, path=(Cell(0, 0), Cell(0, 1))
    )
    snapshot_enter = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=600,
        pending_moves=(move_snap_instant,), jumps=()
    )
    pv_instant = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_enter)
    pv_instant.change_state("move", snapshot_enter)
    snapshot_update = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=400,
        pending_moves=(move_snap_instant,), jumps=()
    )
    pv_instant.update(0.1, snapshot_update)
    assert pv_instant.state.name == "move"

def test_jump_state_logic():
    geometry = BoardGeometry(cell_size=100)
    asset_loader = MagicMock()
    mock_assets = MagicMock()
    mock_assets.config = {"physics": {"next_state_when_finished": "short_rest"}}
    mock_assets.sprites = [MagicMock(spec=Img)]
    asset_loader.get_piece_assets.return_value = mock_assets
    
    board_snap = BoardSnapshot(grid=((None,),), width=1, height=1)
    jump_snap = JumpSnapshot(
        cell=(0, 0), start=0, end=1000,
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    )
    snapshot = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=500,
        pending_moves=(), jumps=(jump_snap,)
    )

    # 1. Normal jump updates height offset
    pv = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot)
    pv.change_state("jump", snapshot)
    pv.update(0.1, snapshot)
    # clock=500, start=0, end=1000 -> progress = 0.5. peak_height=80. height = 4 * 80 * 0.5 * 0.5 = 80
    assert pv.px == 0
    assert pv.py == -80

    # 2. Finished jump (clock >= 1000)
    snapshot_end = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=1000,
        pending_moves=(), jumps=(jump_snap,)
    )
    pv.update(0.1, snapshot_end)
    assert pv.state.name == "short_rest"

    # 3. Active jump disappears
    pv2 = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot)
    pv2.change_state("jump", snapshot)
    snapshot_empty = GameSnapshot(board=board_snap, selected_piece=None, game_over=False, clock=500, pending_moves=(), jumps=())
    pv2.update(0.1, snapshot_empty)
    assert pv2.state.name == "short_rest"

    # 4. Duration <= 0 fallback
    jump_instant = JumpSnapshot(
        cell=(0, 0), start=600, end=500,
        piece=PieceSnapshot(color="w", kind="P", cell=Cell(0, 0))
    )
    snapshot_instant = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=400,
        pending_moves=(), jumps=(jump_instant,)
    )
    pv3 = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_instant)
    pv3.change_state("jump", snapshot_instant)
    pv3.update(0.1, snapshot_instant)
    assert pv3.state.name == "jump"

def test_rest_states_logic():
    geometry = BoardGeometry(cell_size=100)
    asset_loader = MagicMock()
    mock_assets = MagicMock()
    mock_assets.config = {}
    mock_assets.sprites = [MagicMock(spec=Img)]
    asset_loader.get_piece_assets.return_value = mock_assets
    
    # Piece is at (0, 0), cooldown_until is 1000
    p_snap = PieceSnapshot(color="w", kind="P", cell=Cell(0, 0), cooldown_until=1000)
    board_snap = BoardSnapshot(grid=((p_snap,),), width=1, height=1)
    
    # Clock is 500 (still cooling down)
    snapshot_cool = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=500,
        pending_moves=(), jumps=()
    )
    
    pv_short = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_cool)
    pv_short.change_state("short_rest", snapshot_cool)
    
    pv_long = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_cool)
    pv_long.change_state("long_rest", snapshot_cool)

    # Update while still cooling down
    pv_short.update(0.1, snapshot_cool)
    pv_long.update(0.1, snapshot_cool)
    assert pv_short.state.name == "short_rest"
    assert pv_long.state.name == "long_rest"

    # Clock is 1000 (cooldown expired) -> transition to idle
    snapshot_idle = GameSnapshot(
        board=board_snap, selected_piece=None, game_over=False, clock=1000,
        pending_moves=(), jumps=()
    )
    pv_short.update(0.1, snapshot_idle)
    pv_long.update(0.1, snapshot_idle)
    assert pv_short.state.name == "idle"
    assert pv_long.state.name == "idle"

    # Piece view cell is out of bounds or snapshot piece disappears -> rest states handle safely
    snapshot_empty = GameSnapshot(
        board=BoardSnapshot(grid=((None,),), width=1, height=1),
        selected_piece=None, game_over=False, clock=500, pending_moves=(), jumps=()
    )
    
    pv_short_oob = PieceView(color="w", kind="P", cell=Cell(5, 5), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_empty)
    pv_short_oob.change_state("short_rest", snapshot_empty)
    pv_short_oob.update(0.1, snapshot_empty) # should run without crash
    
    pv_long_empty = PieceView(color="w", kind="P", cell=Cell(0, 0), geometry=geometry, asset_loader=asset_loader, snapshot=snapshot_empty)
    pv_long_empty.change_state("long_rest", snapshot_empty)
    pv_long_empty.update(0.1, snapshot_empty) # should return early without crash
    assert pv_long_empty.state.name == "long_rest"
