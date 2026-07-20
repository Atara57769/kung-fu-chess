import logging
from ui.ui_config import LEFT_PADDING, RIGHT_PADDING
from ui.screens.screen_manager import ScreenManager
from ui.screens.home_screen import HomeScreen
from ui.screens.waiting_screen import WaitingScreen
from ui.screens.room_screen import RoomScreen
from ui.screens.online_game_screen import OnlineGameScreen
from ui.board.board_geometry import BoardGeometry
from ui.rendering.renderer import Renderer
from ui.animation.animation_manager import AnimationManager
from network.client import GameClient

class OnlineCoordinator:
    def __init__(self, client: GameClient, screen_manager: ScreenManager, 
                 geometry: BoardGeometry, renderer: Renderer, 
                 animation_manager: AnimationManager) -> None:
        self.client = client
        self.screen_manager = screen_manager
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.logger = logging.getLogger(__name__)

    def setup_screens(self) -> None:
        """Sets up screen objects and maps local UI buttons to client network calls."""
        cell_size = self.geometry.cell_size
        total_w = cell_size * 8 + LEFT_PADDING + RIGHT_PADDING
        total_h = cell_size * 8
        
        def trigger_quick_match():
            self.client.enter_matchmaking()
            waiting = WaitingScreen(self.screen_manager, total_w, total_h)
            waiting.buttons[0].callback = cancel_quick_match
            self.screen_manager.switch_to(waiting)
            
        def cancel_quick_match():
            self.client.leave_matchmaking()
            self.screen_manager.switch_to(home)
            
        def trigger_create_room():
            home.popup.hide()
            self.client.create_room()
            
        def trigger_join_room():
            home.popup.hide()
            print("\n=== JOIN ROOM ===")
            room_id = input("Enter Room ID: ").strip()
            if room_id:
                self.client.join_room(room_id)
                
        home = HomeScreen(self.screen_manager, total_w, total_h, self.client.username, self.client.rating)
        home.buttons[0].callback = trigger_quick_match
        home.popup.buttons_info = [
            ("Create Room", trigger_create_room),
            ("Join Room", trigger_join_room),
            ("Cancel", home._on_close_popup)
        ]
        home.popup.initialized_position = False
        
        self.screen_manager.switch_to(home)

    def check_network_transitions(self) -> None:
        """Polls client room state updates and transitions screens synchronously."""
        if self.client.error_message:
            self.logger.error(f"Server error: {self.client.error_message}")
            self.client.error_message = None
            
        state = self.client.room_state
        curr_screen = self.screen_manager.active_screen
        cell_size = self.geometry.cell_size
        total_w = cell_size * 8 + LEFT_PADDING + RIGHT_PADDING
        total_h = cell_size * 8
        
        if state is None:
            # Check if we were in lobby and need to return home
            if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen) and not isinstance(curr_screen, OnlineGameScreen):
                home = HomeScreen(self.screen_manager, total_w, total_h, self.client.username, self.client.rating)
                self.screen_manager.switch_to(home)
            return
            
        status = state.get("status")
        room_id = state.get("room_id")
        
        if room_id is None:
            if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen):
                home = HomeScreen(self.screen_manager, total_w, total_h, self.client.username, self.client.rating)
                self.screen_manager.switch_to(home)
        elif status == "waiting":
            if not isinstance(curr_screen, RoomScreen):
                is_creator = (state.get("white") == self.client.username)
                room = RoomScreen(
                    self.screen_manager, 
                    total_w, 
                    total_h,
                    room_id=room_id,
                    is_creator=is_creator,
                    white_player=state.get("white"),
                    black_player=state.get("black")
                )
                # Route leave button to client leave API
                for btn in room.buttons:
                    if btn.text == "Leave Lobby":
                        btn.callback = self.client.leave_room
                self.screen_manager.switch_to(room)
            else:
                # Update lobby view
                curr_screen.white_player = state.get("white") or "[Empty]"
                curr_screen.black_player = state.get("black") or "[Empty]"
                curr_screen.labels[1].text = f"White Seat: {curr_screen.white_player}"
                curr_screen.labels[2].text = f"Black Seat: {curr_screen.black_player}"
                curr_screen.spectators = state.get("spectators", [])
                curr_screen.labels[3].text = f"Spectators: {', '.join(curr_screen.spectators) if curr_screen.spectators else 'None'}"
        elif status == "active":
            if not isinstance(curr_screen, OnlineGameScreen):
                online_game = OnlineGameScreen(
                    self.screen_manager,
                    self.client,
                    self.geometry,
                    self.renderer,
                    self.animation_manager
                )
                self.screen_manager.switch_to(online_game)

    def update(self, dt: float) -> None:
        """Checks for network transitions and updates coordinator logic."""
        self.check_network_transitions()
