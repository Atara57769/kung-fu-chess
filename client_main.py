import argparse
import sys
import time
import logging
import cv2
import numpy as np

from constants import DEFAULT_HOST, DEFAULT_PORT, CELL_SIZE
from ui.ui_config import LEFT_PADDING, RIGHT_PADDING, TIME_STEP_MS
from ui.board.board_geometry import BoardGeometry
from ui.assets.asset_loader import AssetLoader
from ui.animation.animation_manager import AnimationManager
from ui.rendering.img import Img
from ui.rendering.window import Window
from ui.rendering.renderer import Renderer
from ui.history.history_tracker import UIHistoryTracker
from services.score_tracker import ScoreTracker
from core.events.event_bus import EventBus
from ui.screens.screen_manager import ScreenManager
from ui.screens.home_screen import HomeScreen
from ui.screens.waiting_screen import WaitingScreen
from ui.screens.room_screen import RoomScreen
from ui.screens.online_game_screen import OnlineGameScreen
from network.client import GameClient

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parses launcher parameters."""
    parser = argparse.ArgumentParser(description="Kung-Fu Chess Client Launcher")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Game Server Host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Game Server Port")
    parser.add_argument("--scale", type=float, default=1.0, help="UI Scale Factor")
    return parser.parse_args()

def run_terminal_login(client: GameClient) -> None:
    """Prompts for user credentials in terminal and authenticates with WebSocket server."""
    print("\n==============================")
    print("    KUNG-FU CHESS ONLINE LOGIN  ")
    print("==============================\n")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("Error: Username and Password cannot be empty.")
        sys.exit(1)
        
    client.authenticate(username, password)
    
    # Wait for response from server auth loop
    start_t = time.time()
    while not client.authenticated and not client.error_message:
        time.sleep(0.1)
        if time.time() - start_t > 5.0:
            print("Authentication timeout. Could not reach server.")
            client.stop()
            sys.exit(1)
            
    if client.error_message:
        print(f"Authentication failed: {client.error_message}")
        client.stop()
        sys.exit(1)
        
    print(f"Authentication success! Welcome {client.username} (ELO: {client.rating})")

def setup_client_screens(client: GameClient, screen_manager: ScreenManager, 
                         geometry: BoardGeometry, renderer: Renderer, 
                         animation_manager: AnimationManager) -> None:
    """Sets up screen objects and maps local UI buttons to client network calls."""
    cell_size = geometry.cell_size
    total_w = cell_size * 8 + LEFT_PADDING + RIGHT_PADDING
    total_h = cell_size * 8
    
    # Configure HomeScreen callbacks
    def trigger_quick_match():
        client.enter_matchmaking()
        waiting = WaitingScreen(screen_manager, total_w, total_h)
        waiting.buttons[0].callback = cancel_quick_match
        screen_manager.switch_to(waiting)
        
    def cancel_quick_match():
        client.leave_matchmaking()
        screen_manager.switch_to(home)
        
    def trigger_create_room():
        home.popup.hide()
        client.create_room()
        
    def trigger_join_room():
        home.popup.hide()
        print("\n=== JOIN ROOM ===")
        room_id = input("Enter Room ID: ").strip()
        if room_id:
            client.join_room(room_id)
            
    home = HomeScreen(screen_manager, total_w, total_h, client.username, client.rating)
    home.buttons[0].callback = trigger_quick_match
    home.popup.buttons_info = [
        ("Create Room", trigger_create_room),
        ("Join Room", trigger_join_room),
        ("Cancel", home._on_close_popup)
    ]
    home.popup.initialized_position = False
    
    screen_manager.switch_to(home)

def check_network_transitions(screen_manager: ScreenManager, client: GameClient, 
                               geometry: BoardGeometry, renderer: Renderer, 
                               animation_manager: AnimationManager) -> None:
    """Polls client room state updates and transitions screens synchronously."""
    if client.error_message:
        logger.error(f"Server error: {client.error_message}")
        client.error_message = None
        
    state = client.room_state
    curr_screen = screen_manager.active_screen
    cell_size = geometry.cell_size
    total_w = cell_size * 8 + LEFT_PADDING + RIGHT_PADDING
    total_h = cell_size * 8
    
    if state is None:
        # Check if we were in lobby and need to return home
        if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen) and not isinstance(curr_screen, OnlineGameScreen):
            home = HomeScreen(screen_manager, total_w, total_h, client.username, client.rating)
            screen_manager.switch_to(home)
        return
        
    status = state.get("status")
    room_id = state.get("room_id")
    
    if room_id is None:
        if not isinstance(curr_screen, HomeScreen) and not isinstance(curr_screen, WaitingScreen):
            home = HomeScreen(screen_manager, total_w, total_h, client.username, client.rating)
            screen_manager.switch_to(home)
    elif status == "waiting":
        if not isinstance(curr_screen, RoomScreen):
            is_creator = (state.get("white") == client.username)
            room = RoomScreen(
                screen_manager, 
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
                    btn.callback = client.leave_room
            screen_manager.switch_to(room)
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
                screen_manager,
                client,
                geometry,
                renderer,
                animation_manager
            )
            screen_manager.switch_to(online_game)

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    args = parse_args()
    
    # 1. Start network client
    client = GameClient(host=args.host, port=args.port)
    client.start()
    
    try:
        # 2. Run credentials check
        run_terminal_login(client)
        
        # 3. Setup assets
        cell_size = int(CELL_SIZE * args.scale)
        geometry = BoardGeometry(cell_size)
        
        asset_loader = AssetLoader(
            piece_size=(cell_size, cell_size),
            board_size=(8 * cell_size, 8 * cell_size)
        )
        logger.info("Loading graphic sprites...")
        asset_loader.load_all()
        
        # 4. Setup renderer details
        event_bus = EventBus()
        score_tracker = ScoreTracker(event_bus)
        history_tracker = UIHistoryTracker()
        
        animation_manager = AnimationManager(geometry, asset_loader)
        window = Window(title=f"Kung-Fu Chess Online: {client.username}")
        
        renderer = Renderer(
            asset_loader,
            geometry,
            history_tracker=history_tracker,
            left_padding=LEFT_PADDING,
            right_padding=RIGHT_PADDING,
            score_tracker=score_tracker
        )
        
        # 5. Initialize ScreenManager & setup home Screen
        screen_manager = ScreenManager()
        setup_client_screens(client, screen_manager, geometry, renderer, animation_manager)
        
        # 6. OpenCV Mouse Callback bindings
        cv2.namedWindow("Image")
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                screen_manager.handle_click(x, y, is_right=False)
            elif event == cv2.EVENT_RBUTTONDOWN:
                screen_manager.handle_click(x, y, is_right=True)
            elif event == cv2.EVENT_MOUSEMOVE:
                screen_manager.handle_mouse_move(x, y)
        cv2.setMouseCallback("Image", on_mouse)
        
        # 7. GUI Loop
        logger.info("Starting online visual frame loop...")
        running = True
        while running:
            dt = TIME_STEP_MS / 1000.0
            
            # Transition screen active states if updates received
            check_network_transitions(screen_manager, client, geometry, renderer, animation_manager)
            
            # Tick screen logic
            screen_manager.update(dt)
            
            # Render & Display canvas
            canvas = Img()
            screen_manager.render(canvas)
            window.display(canvas, TIME_STEP_MS)
            
            try:
                if cv2.getWindowProperty("Image", cv2.WND_PROP_VISIBLE) < 1:
                    running = False
            except Exception:
                pass
                
    finally:
        logger.info("Shutting down online chess client...")
        client.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
