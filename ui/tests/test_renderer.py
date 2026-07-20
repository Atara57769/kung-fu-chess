import pytest
import numpy as np
from unittest.mock import MagicMock
from models.cell import Cell
from models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
from ui.rendering.renderer import Renderer
from ui.rendering.img import Img

def test_renderer_initialization():
    asset_loader = MagicMock()
    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)
    assert renderer.left_padding == 10
    assert renderer.right_padding == 20

def test_render_basic_board():
    # Setup mock asset loader
    bg_img = Img()
    bg_img.img = np.zeros((100, 100, 3), dtype=np.uint8)
    asset_loader = MagicMock()
    asset_loader.get_board_background.return_value = bg_img

    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)

    # Mock snapshot
    grid = tuple(tuple(None for _ in range(8)) for _ in range(8))
    board_snap = BoardSnapshot(grid=grid, width=8, height=8)
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )

    canvas = renderer.render(snapshot, active_views=[])
    assert isinstance(canvas, Img)
    # total_w = board_w (100) + left_padding (10) + right_padding (20) = 130
    assert canvas.img.shape == (100, 130, 3)

def test_render_with_active_views_and_overlays():
    # Setup mock asset loader
    bg_img = Img()
    bg_img.img = np.zeros((100, 100, 3), dtype=np.uint8)
    asset_loader = MagicMock()
    asset_loader.get_board_background.return_value = bg_img

    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)

    # Mock piece snap
    p_snap = PieceSnapshot(color='w', kind='N', cell=Cell(0, 0))
    grid = [[None for _ in range(8)] for _ in range(8)]
    grid[0][0] = p_snap
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)

    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=p_snap,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )

    # Mock active view
    mock_view = MagicMock()
    mock_view.px = 5
    mock_view.py = 5
    mock_view.cell = Cell(0, 0)
    mock_view.color = 'w'
    mock_view.kind = 'N'
    
    mock_sprite = MagicMock()
    mock_view.get_sprite.return_value = mock_sprite

    # Render with active views
    canvas = renderer.render(snapshot, active_views=[mock_view])
    
    # Verify sprite was drawn on canvas
    mock_sprite.draw_on.assert_called_once()
    draw_args = mock_sprite.draw_on.call_args[0]
    assert draw_args[0] == canvas
    # px + left_padding = 5 + 10 = 15
    assert draw_args[1] == 15
    assert draw_args[2] == 5

def test_render_with_cooldown():
    # Setup mock asset loader
    bg_img = Img()
    bg_img.img = np.zeros((100, 100, 3), dtype=np.uint8)
    asset_loader = MagicMock()
    asset_loader.get_board_background.return_value = bg_img

    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)

    # Piece on cooldown (cooldown_until=500, clock=200)
    p_snap = PieceSnapshot(color='w', kind='N', cell=Cell(0, 0), cooldown_until=500)
    grid = [[None for _ in range(8)] for _ in range(8)]
    grid[0][0] = p_snap
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)

    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=200,
        pending_moves=(),
        jumps=()
    )

    # Mock active view
    mock_view = MagicMock()
    mock_view.px = 5
    mock_view.py = 5
    mock_view.cell = Cell(0, 0)
    mock_view.color = 'w'
    mock_view.kind = 'N'
    
    mock_sprite = MagicMock()
    mock_view.get_sprite.return_value = mock_sprite

    # Render
    canvas = renderer.render(snapshot, active_views=[mock_view])
    # The draw_on should be called
    mock_sprite.draw_on.assert_called_once()

def test_render_game_over():
    # Setup mock asset loader
    bg_img = Img()
    bg_img.img = np.zeros((100, 100, 3), dtype=np.uint8)
    asset_loader = MagicMock()
    asset_loader.get_board_background.return_value = bg_img

    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)

    grid = tuple(tuple(None for _ in range(8)) for _ in range(8))
    board_snap = BoardSnapshot(grid=grid, width=8, height=8)
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=True,
        clock=0,
        pending_moves=(),
        jumps=()
    )

    canvas = renderer.render(snapshot, active_views=[])
    assert canvas.img.shape == (100, 130, 3)

def test_history_renderer():
    from ui.rendering.history_renderer import HistoryRenderer
    history_tracker = MagicMock()
    history_tracker.history = [
        {'color': 'w', 'kind': 'N', 'time': 1000, 'to_pos': Cell(0, 0)}
    ]
    
    hist_renderer = HistoryRenderer(history_tracker, left_padding=50, right_padding=50)
    canvas = Img()
    canvas.img = np.zeros((200, 300, 3), dtype=np.uint8)
    
    grid = tuple(tuple(None for _ in range(8)) for _ in range(8))
    board_snap = BoardSnapshot(grid=grid, width=8, height=8)
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )
    
    # Render history panels
    hist_renderer.draw_history_panels(canvas, snapshot, board_w=200, board_h=200, total_w=300)
    
    # Verify that the canvas image was not corrupted and retains dimensions
    assert canvas.img.shape == (200, 300, 3)


def test_history_renderer_score_calculation():
    from ui.rendering.history_renderer import HistoryRenderer
    from ui.ui_config import PIECE_POINTS
    history_tracker = MagicMock()
    history_tracker.history = []
    
    hist_renderer = HistoryRenderer(history_tracker, left_padding=50, right_padding=50)
    canvas = Img()
    canvas.img = np.zeros((200, 300, 3), dtype=np.uint8)
    
    # Grid with 1 White Queen, 2 Black Rooks, 1 White Pawn
    grid = [[None for _ in range(8)] for _ in range(8)]
    grid[0][0] = PieceSnapshot(color='w', kind='Q', cell=Cell(0, 0))
    grid[0][1] = PieceSnapshot(color='w', kind='P', cell=Cell(1, 0))
    grid[1][0] = PieceSnapshot(color='b', kind='R', cell=Cell(0, 1))
    grid[1][1] = PieceSnapshot(color='b', kind='R', cell=Cell(1, 1))
    
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )
    
    # Track call args to canvas.put_text
    canvas.put_text = MagicMock()
    
    hist_renderer.draw_history_panels(canvas, snapshot, board_w=200, board_h=200, total_w=300)
    
    # White score should be: Q (9) + P (1) = 10
    # Black score should be: R (5) + R (5) = 10
    
    calls = canvas.put_text.call_args_list
    white_title_call = [c for c in calls if "White (" in c[0][0]]
    black_title_call = [c for c in calls if "Black (" in c[0][0]]
    
    assert len(white_title_call) == 1
    assert white_title_call[0][0][0] == "White (10)"
    
    assert len(black_title_call) == 1
    assert black_title_call[0][0][0] == "Black (10)"

def test_renderer_4_channel():
    # Setup mock asset loader with 4 channel background
    bg_img = Img()
    bg_img.img = np.zeros((100, 100, 4), dtype=np.uint8)
    asset_loader = MagicMock()
    asset_loader.get_board_background.return_value = bg_img

    geometry = MagicMock()
    geometry.cell_size = 100
    renderer = Renderer(asset_loader, geometry, left_padding=10, right_padding=20)

    grid = tuple(tuple(None for _ in range(8)) for _ in range(8))
    board_snap = BoardSnapshot(grid=grid, width=8, height=8)
    snapshot = GameSnapshot(
        board=board_snap,
        selected_piece=None,
        game_over=False,
        clock=0,
        pending_moves=(),
        jumps=()
    )

    canvas = renderer.render(snapshot, active_views=[])
    assert canvas.img.shape == (100, 130, 4)


