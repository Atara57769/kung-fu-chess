import logging
from typing import Optional, Any

from client.ui.ui_config import LEFT_PADDING, RIGHT_PADDING
from client.ui.screens.base_screen import ScreenType
from client.ui.screens.screen_manager import ScreenManager
from client.ui.screens.home_screen import HomeScreen
from client.ui.screens.waiting_screen import WaitingScreen
from client.ui.screens.room_screen import RoomScreen
from client.ui.screens.online_game_screen import OnlineGameScreen
from client.ui.board.board_geometry import BoardGeometry
from client.ui.rendering.game_renderer import GameRenderer
from client.ui.animation.animation_manager import AnimationManager
from client.ui.components.popup_dialog import show_error_dialog, show_warning_dialog
from client.network.base_client import BaseGameClient
from shared.protocol import (
    MessageType, BaseMessage, RoomStateMessage, ErrorMessage, MatchmakingTimeoutMessage
)
from shared.constants import (
    ROOM_STATUS_WAITING, ROOM_STATUS_ACTIVE, BOARD_DIMENSION
)

EMPTY_PLAYER = "[Empty]"
WHITE_SEAT_PREFIX = "White Seat: "
BLACK_SEAT_PREFIX = "Black Seat: "
SPECTATORS_PREFIX = "Spectators: "
SPECTATORS_SEPARATOR = ", "
SPECTATORS_NONE = "None"
ERROR_DIALOG_TITLE = "Error"
SERVER_ERROR_LOG_PREFIX = "Server error: "
MATCHMAKING_TIMEOUT_TITLE = "Matchmaking Timeout"
MATCHMAKING_TIMEOUT_MSG = "No opponent was found. Please try again."


class OnlineCoordinator:
    def __init__(self, client: BaseGameClient, screen_manager: ScreenManager, 
                 geometry: BoardGeometry, renderer: GameRenderer, 
                 animation_manager: AnimationManager) -> None:
        self.client = client
        self.screen_manager = screen_manager
        self.geometry = geometry
        self.renderer = renderer
        self.animation_manager = animation_manager
        self.logger = logging.getLogger(__name__)
        
        self._pending_events: list[tuple[MessageType, BaseMessage]] = []
        self.client.pubsub.subscribe(MessageType.ROOM_STATE, self._on_room_state)
        self.client.pubsub.subscribe(MessageType.ERROR, self._on_error)
        self.client.pubsub.subscribe(MessageType.MATCHMAKING_STATUS, self._on_matchmaking_status)
        self.client.pubsub.subscribe(MessageType.MATCHMAKING_TIMEOUT, self._on_matchmaking_timeout)

    def _on_room_state(self, state: RoomStateMessage) -> None:
        self._pending_events.append((MessageType.ROOM_STATE, state))

    def _on_error(self, msg: ErrorMessage) -> None:
        self._pending_events.append((MessageType.ERROR, msg))

    def _on_matchmaking_status(self, data: MatchmakingStatusMessage) -> None:
        self._pending_events.append((MessageType.MATCHMAKING_STATUS, data))

    def _on_matchmaking_timeout(self, data: MatchmakingTimeoutMessage) -> None:
        self._pending_events.append((MessageType.MATCHMAKING_TIMEOUT, data))


    def _create_online_home_screen(self) -> HomeScreen:
        """Helper to construct HomeScreen with online match and custom room callbacks."""
        cell_size = self.geometry.cell_size
        total_w = cell_size * BOARD_DIMENSION + LEFT_PADDING + RIGHT_PADDING
        total_h = cell_size * BOARD_DIMENSION
        
        def trigger_quick_match():
            self.client.join_matchmaking()
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

    def _handle_room_state_change(self, state: Optional[RoomStateMessage]) -> None:
        """Transitions screen states based on room status updates."""
        curr_screen = self.screen_manager.active_screen
        cell_size = self.geometry.cell_size
        total_w = cell_size * BOARD_DIMENSION + LEFT_PADDING + RIGHT_PADDING
        total_h = cell_size * BOARD_DIMENSION
        
        if state is None or state.room_id is None:
            self._handle_no_room_state(curr_screen)
            return

        if state.status == ROOM_STATUS_WAITING:
            self._handle_waiting_room_state(state, curr_screen, total_w, total_h)
        elif state.status == ROOM_STATUS_ACTIVE:
            self._handle_active_room_state(curr_screen)

    def _handle_no_room_state(self, curr_screen: Optional[Any]) -> None:
        """Handles screen fallback to home when there is no room state or room_id is missing."""
        if curr_screen and curr_screen.screen_type not in (ScreenType.HOME, ScreenType.WAITING, ScreenType.ONLINE_GAME):
            home = self._create_online_home_screen()
            self.screen_manager.switch_to(home)

    def _handle_waiting_room_state(self, state: RoomStateMessage, curr_screen: Optional[Any], total_w: int, total_h: int) -> None:
        """Handles screen transitions and UI label updates for waiting rooms."""
        white_player = state.white
        black_player = state.black
        spectators = state.spectators

        if not curr_screen or curr_screen.screen_type != ScreenType.ROOM:
            is_creator = (white_player == self.client.username)
            room = RoomScreen(
                self.screen_manager, 
                total_w, 
                total_h,
                room_id=state.room_id,
                is_creator=is_creator,
                white_player=white_player,
                black_player=black_player,
                client=self.client
            )
            self.screen_manager.switch_to(room)
        else:
            curr_screen.white_player = white_player or EMPTY_PLAYER
            curr_screen.black_player = black_player or EMPTY_PLAYER
            curr_screen.labels[1].text = f"{WHITE_SEAT_PREFIX}{curr_screen.white_player}"
            curr_screen.labels[2].text = f"{BLACK_SEAT_PREFIX}{curr_screen.black_player}"
            curr_screen.spectators = spectators or []
            specs_joined = SPECTATORS_SEPARATOR.join(curr_screen.spectators) if curr_screen.spectators else SPECTATORS_NONE
            curr_screen.labels[3].text = f"{SPECTATORS_PREFIX}{specs_joined}"

    def _handle_active_room_state(self, curr_screen: Optional[Any]) -> None:
        """Handles screen transition when the game room becomes active."""
        if not curr_screen or curr_screen.screen_type != ScreenType.ONLINE_GAME:
            online_game = OnlineGameScreen(
                self.screen_manager,
                self.client,
                self.geometry,
                self.renderer,
                self.animation_manager
            )
            self.screen_manager.switch_to(online_game)

    def _handle_error_message(self, msg: ErrorMessage) -> None:
        if msg.message:
            self.logger.error(f"{SERVER_ERROR_LOG_PREFIX}{msg.message}")
            show_error_dialog(ERROR_DIALOG_TITLE, msg.message)

    def _handle_matchmaking_timeout(self, data: MatchmakingTimeoutMessage) -> None:
        curr_screen = self.screen_manager.active_screen
        if curr_screen and curr_screen.screen_type == ScreenType.WAITING:
            home = self._create_online_home_screen()
            self.screen_manager.switch_to(home)
        msg_text = getattr(data, "message", None) or MATCHMAKING_TIMEOUT_MSG
        show_warning_dialog(MATCHMAKING_TIMEOUT_TITLE, msg_text)


    def update(self, dt: float) -> None:
        """Processes any queued network events on the main render thread."""
        events_to_process = list(self._pending_events)
        self._pending_events.clear()
        
        for event_type, payload in events_to_process:
            if event_type == MessageType.ROOM_STATE:
                self._handle_room_state_change(payload)
            elif event_type == MessageType.ERROR:
                self._handle_error_message(payload)
            elif event_type == MessageType.MATCHMAKING_TIMEOUT:
                self._handle_matchmaking_timeout(payload)
