import logging
from typing import Optional
from client.ui.ui_config import LEFT_PADDING, RIGHT_PADDING
from client.ui.screens.screen_manager import ScreenManager
from client.ui.screens.home_screen import HomeScreen
from client.ui.screens.waiting_screen import WaitingScreen
from client.ui.screens.room_screen import RoomScreen
from client.ui.screens.online_game_screen import OnlineGameScreen
from client.ui.board.board_geometry import BoardGeometry
from client.ui.rendering.game_renderer import GameRenderer
from client.ui.animation.animation_manager import AnimationManager
from client.network.client import GameClient
from shared.protocol import MessageType
from shared.constants import (
    ROOM_STATUS_WAITING, ROOM_STATUS_ACTIVE,
    FIELD_STATUS, FIELD_ROOM_ID, FIELD_WHITE, FIELD_BLACK, FIELD_SPECTATORS
)

class OnlineCoordinator:
    def __init__(self, client: GameClient, screen_manager: ScreenManager, 
                 geometry: BoardGeometry, renderer: GameRenderer, 
                 animation_manager: AnimationManager) -> None:
        self.client = client
        self.screen_manager = screen_manager
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.logger = logging.getLogger(__name__)
        
        self._pending_events: list = []
        self.client.pubsub.subscribe(MessageType.ROOM_STATE, self._on_room_state)
        self.client.pubsub.subscribe(MessageType.ERROR, self._on_error)

    def _on_room_state(self, state: dict) -> None:
        self._pending_events.append((MessageType.ROOM_STATE, state))

    def _on_error(self, message: str) -> None:
        self._pending_events.append((MessageType.ERROR, message))

    def _create_online_home_screen(self) -> HomeScreen:
        """Helper to construct HomeScreen with online match and custom room callbacks."""
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

        home = HomeScreen(self.screen_manager, total_w, total_h, self.client.username, self.client.rating, client=self.client)
        home.buttons[0].callback = trigger_quick_match
        return home

    def setup_screens(self) -> None:
        """Sets up screen objects and maps local UI buttons to client network calls."""
        home = self._create_online_home_screen()
        self.screen_manager.switch_to(home)

    def _handle_room_state_change(self, state: Optional[dict]) -> None:
        """Transitions screen states based on room status updates."""
        curr_screen = self.screen_manager.active_screen
        cell_size = self.geometry.cell_size
        total_w = cell_size * 8 + LEFT_PADDING + RIGHT_PADDING
        total_h = cell_size * 8
        
        if state is None:
            if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen) and not isinstance(curr_screen, OnlineGameScreen):
                home = self._create_online_home_screen()
                self.screen_manager.switch_to(home)
            return
            
        status = state.get(FIELD_STATUS)
        room_id = state.get(FIELD_ROOM_ID)
        
        if room_id is None:
            if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen):
                home = self._create_online_home_screen()
                self.screen_manager.switch_to(home)
        elif status == ROOM_STATUS_WAITING:
            if not isinstance(curr_screen, RoomScreen):
                is_creator = (state.get(FIELD_WHITE) == self.client.username)
                room = RoomScreen(
                    self.screen_manager, 
                    total_w, 
                    total_h,
                    room_id=room_id,
                    is_creator=is_creator,
                    white_player=state.get(FIELD_WHITE),
                    black_player=state.get(FIELD_BLACK),
                    client=self.client
                )
                self.screen_manager.switch_to(room)
            else:
                curr_screen.white_player = state.get(FIELD_WHITE) or "[Empty]"
                curr_screen.black_player = state.get(FIELD_BLACK) or "[Empty]"
                curr_screen.labels[1].text = f"White Seat: {curr_screen.white_player}"
                curr_screen.labels[2].text = f"Black Seat: {curr_screen.black_player}"
                curr_screen.spectators = state.get(FIELD_SPECTATORS, [])
                curr_screen.labels[3].text = f"Spectators: {', '.join(curr_screen.spectators) if curr_screen.spectators else 'None'}"
        elif status == ROOM_STATUS_ACTIVE:
            if not isinstance(curr_screen, OnlineGameScreen):
                online_game = OnlineGameScreen(
                    self.screen_manager,
                    self.client,
                    self.geometry,
                    self.renderer,
                    self.animation_manager
                )
                self.screen_manager.switch_to(online_game)

    def _handle_error_message(self, message: str) -> None:
        if message:
            self.logger.error(f"Server error: {message}")

    def update(self, dt: float) -> None:
        """Processes any queued network events on the main render thread."""
        events_to_process = list(self._pending_events)
        self._pending_events.clear()
        
        for event_type, payload in events_to_process:
            if event_type == MessageType.ROOM_STATE:
                self._handle_room_state_change(payload)
            elif event_type == MessageType.ERROR:
                self._handle_error_message(payload)
