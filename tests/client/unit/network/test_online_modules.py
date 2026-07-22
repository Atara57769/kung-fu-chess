import pytest
import sys
from unittest.mock import MagicMock, patch, call
from client.ui.app.terminal_login import run_terminal_login
from client.ui.app.online_coordinator import OnlineCoordinator
from client.ui.app.online_runner import OnlineUIRunner
from client.ui.screens.home_screen import HomeScreen
from client.ui.screens.waiting_screen import WaitingScreen
from client.ui.screens.room_screen import RoomScreen
from client.ui.screens.online_game_screen import OnlineGameScreen

class DummyClient:
    def __init__(self):
        from client.services.client_pubsub import ClientPubSub
        self.pubsub = ClientPubSub()
        self.authenticated = False
        self.error_message = None
        self.username = "test_player"
        self.rating = 1500
        self.room_state = None
        self.calls = []

    def authenticate(self, username, password):
        self.calls.append(('authenticate', username, password))

    def enter_matchmaking(self):
        self.calls.append('enter_matchmaking')

    def leave_matchmaking(self):
        self.calls.append('leave_matchmaking')

    def create_room(self, room_id=None):
        self.calls.append(('create_room', room_id) if room_id else 'create_room')

    def join_room(self, room_id):
        self.calls.append(('join_room', room_id))

    def leave_room(self):
        self.calls.append('leave_room')

    def stop(self):
        self.calls.append('stop')

def test_terminal_login_success():
    client = DummyClient()
    
    # Mock inputs and authenticate callback to succeed immediately
    def side_effect(username, password):
        client.authenticated = True

    client.authenticate = side_effect
    
    with patch('builtins.input', side_effect=["test_user", "test_pw"]):
        run_terminal_login(client)
        
    assert client.authenticated is True

def test_terminal_login_empty_credentials():
    client = DummyClient()
    with patch('builtins.input', side_effect=["", "test_pw"]):
        with pytest.raises(SystemExit):
            run_terminal_login(client)

def test_terminal_login_timeout():
    client = DummyClient()
    # Mock timeout
    with patch('builtins.input', side_effect=["test_user", "test_pw"]):
        with patch('time.time', side_effect=[0.0, 1.0, 6.0]):
            with patch('time.sleep', return_value=None):
                with pytest.raises(SystemExit):
                    run_terminal_login(client)
    assert 'stop' in client.calls

def test_online_coordinator_setup():
    client = DummyClient()
    screen_manager = MagicMock()
    geometry = MagicMock()
    geometry.cell_size = 60
    renderer = MagicMock()
    animation_manager = MagicMock()
    
    coordinator = OnlineCoordinator(client, screen_manager, geometry, renderer, animation_manager)
    coordinator.setup_screens()
    
    assert screen_manager.switch_to.called
    initial_screen = screen_manager.switch_to.call_args[0][0]
    assert isinstance(initial_screen, HomeScreen)
    assert initial_screen.username == "test_player"
    assert initial_screen.rating == 1500

    quick_match_btn_callback = initial_screen.buttons[0].callback
    quick_match_btn_callback()
    
    assert 'enter_matchmaking' in client.calls
    waiting_screen = screen_manager.switch_to.call_args[0][0]
    assert isinstance(waiting_screen, WaitingScreen)

    cancel_btn_callback = waiting_screen.buttons[0].callback
    cancel_btn_callback()
    assert 'leave_matchmaking' in client.calls
    
    with patch('client.ui.screens.home_screen.RoomDialog') as MockRoomDialog:
        # Mock Create Room flow
        mock_dialog = MagicMock()
        mock_dialog.result_action = "create"
        mock_dialog.room_name = "room123"
        MockRoomDialog.return_value = mock_dialog
        
        initial_screen.buttons[1].callback()  
        assert ('create_room', 'room123') in client.calls
        
        # Mock Join Room flow
        mock_dialog.result_action = "join"
        mock_dialog.room_name = "room123"
        
        initial_screen.buttons[1].callback()  # _on_custom_room_click
        assert ('join_room', 'room123') in client.calls

def test_online_coordinator_transitions():
    client = DummyClient()
    screen_manager = MagicMock()
    screen_manager.active_screen = HomeScreen(screen_manager, 480, 480, "test_player", 1500)
    geometry = MagicMock()
    geometry.cell_size = 60
    renderer = MagicMock()
    animation_manager = MagicMock()
    
    coordinator = OnlineCoordinator(client, screen_manager, geometry, renderer, animation_manager)
    
    from shared.protocol import RoomStateMessage
    
    # 1. Transition to Waiting Room Screen
    client.room_state = RoomStateMessage(
        status="waiting",
        room_id="room_xyz",
        white="test_player",
        black=None,
        spectators=[]
    )
    client.pubsub.publish("room_state", client.room_state)
    
    coordinator.update(0.1)
    
    assert screen_manager.switch_to.called
    room_screen = screen_manager.switch_to.call_args[0][0]
    assert isinstance(room_screen, RoomScreen)
    assert room_screen.room_id == "room_xyz"
    assert room_screen.is_creator is True
    assert room_screen.client is client
    
    # Test Leave Lobby button
    assert len(room_screen.buttons) == 1
    assert room_screen.buttons[0].text == "Leave Lobby"
    room_screen.buttons[0].callback()
    assert 'leave_room' in client.calls

    # Update active screen to be the RoomScreen
    screen_manager.active_screen = room_screen
    
    # 2. Update player joining state
    client.room_state = RoomStateMessage(
        status="waiting",
        room_id="room_xyz",
        white="test_player",
        black="opponent_player",
        spectators=["spec1"]
    )
    client.pubsub.publish("room_state", client.room_state)
    coordinator.update(0.1)
    
    assert room_screen.black_player == "opponent_player"
    assert room_screen.spectators == ["spec1"]

    # 3. Transition to Active game screen
    client.room_state = RoomStateMessage(
        status="active",
        room_id="room_xyz",
        white="test_player",
        black="opponent_player",
        spectators=[]
    )
    client.pubsub.publish("room_state", client.room_state)
    coordinator.update(0.1)
    
    game_screen = screen_manager.switch_to.call_args_list[-1][0][0]
    assert isinstance(game_screen, OnlineGameScreen)


@patch('cv2.namedWindow')
@patch('cv2.setMouseCallback')
@patch('cv2.getWindowProperty')
def test_online_runner_loop(mock_get_window, mock_set_mouse, mock_named_win):
    client = DummyClient()
    screen_manager = MagicMock()
    window = MagicMock()
    coordinator = MagicMock()
    
    runner = OnlineUIRunner(client, screen_manager, window, coordinator, time_step_ms=16)
    
    # Mock window visibility property check: return 1 first (visible), then 0 (closed) to break the loop
    mock_get_window.side_effect = [1, 0]
    
    runner.start_loop()
    
    # Verify loop drove update/render cycles
    assert coordinator.update.call_count == 2
    assert screen_manager.update.call_count == 2
    assert screen_manager.render.call_count == 2
    assert window.display.call_count == 2
    
    # Verify mouse callback registration
    mock_named_win.assert_called_once_with("Image")
    mock_set_mouse.assert_called_once_with("Image", runner._on_mouse_event)

def test_online_game_screen_history_tracker_update():
    from client.ui.screens.online_game_screen import OnlineGameScreen
    screen_manager = MagicMock()
    client = MagicMock()
    # Mock snapshot
    snapshot = MagicMock()
    client.current_snapshot = snapshot
    
    geometry = MagicMock()
    renderer = MagicMock()
    # Setup history tracker on mock renderer
    mock_history_tracker = MagicMock()
    renderer.history_tracker = mock_history_tracker
    animation_manager = MagicMock()
    
    # Initialize game screen
    game_screen = OnlineGameScreen(
        screen_manager, client, geometry, renderer, animation_manager
    )
    
    assert game_screen.history_tracker == mock_history_tracker
    
    # Update game screen
    game_screen.update(0.016)
    
    # Verify history tracker is updated with current snapshot
    mock_history_tracker.update.assert_called_once_with(snapshot)

def test_online_game_screen_local_selection_and_move():
    from client.ui.screens.online_game_screen import OnlineGameScreen
    from shared.models.cell import Cell
    from shared.models.color import Color
    from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
    
    screen_manager = MagicMock()
    client = MagicMock()
    client.game_over_result = None
    client.your_color = Color.WHITE

    # Create 8x8 grid snapshot with a white piece at Cell(6, 4)
    grid = [[None for _ in range(8)] for _ in range(8)]
    p = PieceSnapshot(color=Color.WHITE, kind="P", cell=Cell(6, 4))
    grid[6][4] = p
    board_snap = BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8)
    snapshot = GameSnapshot(board=board_snap, selected_piece=None, game_over=False, clock=0, pending_moves=(), jumps=())
    client.current_snapshot = snapshot

    geometry = MagicMock()
    geometry.pixel_to_cell.side_effect = lambda x, y: Cell(y // 60, x // 60)
    renderer = MagicMock()
    renderer.left_padding = 0
    animation_manager = MagicMock()

    screen = OnlineGameScreen(screen_manager, client, geometry, renderer, animation_manager)

    # First click on white piece (cell (6, 4) -> x=240, y=360)
    screen.handle_click(240, 360)
    assert screen.selected_cell == Cell(6, 4)
    assert client.send_move.call_count == 0

    # Add second white piece at Cell(6, 0)
    p2 = PieceSnapshot(color=Color.WHITE, kind="R", cell=Cell(6, 0))
    grid[6][0] = p2
    snapshot = GameSnapshot(board=BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8), selected_piece=None, game_over=False, clock=0, pending_moves=(), jumps=())
    client.current_snapshot = snapshot

    # Click on second white piece -> switches selection to Cell(6, 0) without sending move
    screen.handle_click(0, 360)
    assert screen.selected_cell == Cell(6, 0)
    assert client.send_move.call_count == 0

    # Click on empty cell (4, 0) (x=0, y=240) -> sends move from Cell(6, 0) to Cell(4, 0)
    screen.handle_click(0, 240)
    assert screen.selected_cell is None
    client.send_move.assert_called_once_with(Cell(6, 0), Cell(4, 0))


def test_online_game_screen_clears_selection_when_piece_captured():
    import numpy as np
    from client.ui.screens.online_game_screen import OnlineGameScreen
    from shared.models.cell import Cell
    from shared.models.color import Color
    from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot
    from client.ui.rendering.img import Img
    
    screen_manager = MagicMock()
    client = MagicMock()
    client.game_over_result = None
    client.countdown_seconds = 0
    client.your_color = Color.WHITE

    # White piece at Cell(6, 4)
    grid = [[None for _ in range(8)] for _ in range(8)]
    grid[6][4] = PieceSnapshot(color=Color.WHITE, kind="P", cell=Cell(6, 4))
    snapshot1 = GameSnapshot(board=BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8), selected_piece=None, game_over=False, clock=0, pending_moves=(), jumps=())
    client.current_snapshot = snapshot1

    geometry = MagicMock()
    geometry.pixel_to_cell.side_effect = lambda x, y: Cell(y // 60, x // 60)
    renderer = MagicMock()
    renderer.left_padding = 0
    res_img = Img()
    res_img.img = np.zeros((480, 800, 3), dtype=np.uint8)
    renderer.render.return_value = res_img
    animation_manager = MagicMock()

    screen = OnlineGameScreen(screen_manager, client, geometry, renderer, animation_manager)

    # Click on white piece -> selects Cell(6, 4)
    screen.handle_click(240, 360)
    assert screen.selected_cell == Cell(6, 4)

    # Piece is captured: grid[6][4] becomes None in new snapshot
    grid[6][4] = None
    snapshot2 = GameSnapshot(board=BoardSnapshot(grid=tuple(tuple(r) for r in grid), width=8, height=8), selected_piece=None, game_over=False, clock=0, pending_moves=(), jumps=())
    client.current_snapshot = snapshot2

    # render() detects piece at selected_cell is missing and resets selection
    canvas = Img()
    screen.render(canvas)
    assert screen.selected_cell is None



