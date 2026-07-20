import pytest
import sys
from unittest.mock import MagicMock, patch, call
from ui.app.terminal_login import run_terminal_login
from ui.app.online_coordinator import OnlineCoordinator
from ui.app.online_runner import OnlineUIRunner
from ui.screens.home_screen import HomeScreen
from ui.screens.waiting_screen import WaitingScreen
from ui.screens.room_screen import RoomScreen
from ui.screens.online_game_screen import OnlineGameScreen

class DummyClient:
    def __init__(self):
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

    # Test matchmaking trigger
    quick_match_btn_callback = initial_screen.buttons[0].callback
    quick_match_btn_callback()
    
    assert 'enter_matchmaking' in client.calls
    # Should have switched to waiting screen
    waiting_screen = screen_manager.switch_to.call_args[0][0]
    assert isinstance(waiting_screen, WaitingScreen)

    # Test cancel matchmaking
    cancel_btn_callback = waiting_screen.buttons[0].callback
    cancel_btn_callback()
    assert 'leave_matchmaking' in client.calls
    
    # Test custom room flow by patching RoomDialog
    with patch('ui.components.room_dialog.RoomDialog') as MockRoomDialog:
        # Mock Create Room flow
        mock_dialog = MagicMock()
        mock_dialog.result_action = "create"
        mock_dialog.room_name = "room123"
        MockRoomDialog.return_value = mock_dialog
        
        initial_screen.buttons[1].callback()  # _on_custom_room_click
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
    
    # 1. Transition to Waiting Room Screen
    client.room_state = {
        "status": "waiting",
        "room_id": "room_xyz",
        "white": "test_player",
        "black": None,
        "spectators": []
    }
    
    coordinator.update(0.1)
    
    assert screen_manager.switch_to.called
    room_screen = screen_manager.switch_to.call_args[0][0]
    assert isinstance(room_screen, RoomScreen)
    assert room_screen.room_id == "room_xyz"
    assert room_screen.is_creator is True
    
    # Update active screen to be the RoomScreen
    screen_manager.active_screen = room_screen
    
    # 2. Update player joining state
    client.room_state = {
        "status": "waiting",
        "room_id": "room_xyz",
        "white": "test_player",
        "black": "opponent_player",
        "spectators": ["spec1"]
    }
    coordinator.update(0.1)
    
    assert room_screen.black_player == "opponent_player"
    assert room_screen.spectators == ["spec1"]

    # 3. Transition to Active game screen
    client.room_state = {
        "status": "active",
        "room_id": "room_xyz",
        "white": "test_player",
        "black": "opponent_player"
    }
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
    from ui.screens.online_game_screen import OnlineGameScreen
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
