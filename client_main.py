import argparse
import sys
import logging
import cv2
from constants import DEFAULT_HOST, DEFAULT_PORT, CELL_SIZE
from ui.ui_config import LEFT_PADDING, RIGHT_PADDING, TIME_STEP_MS
from ui.board.board_geometry import BoardGeometry
from ui.assets.asset_loader import AssetLoader
from ui.animation.animation_manager import AnimationManager
from ui.rendering.window import Window
from ui.rendering.renderer import Renderer
from ui.history.history_tracker import UIHistoryTracker
from services.score_tracker import ScoreTracker
from core.events.event_bus import EventBus
from ui.screens.screen_manager import ScreenManager
from network.client import GameClient

from ui.app.terminal_login import run_terminal_login
from ui.app.online_coordinator import OnlineCoordinator
from ui.app.online_runner import OnlineUIRunner

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parses launcher parameters."""
    parser = argparse.ArgumentParser(description="Kung-Fu Chess Client Launcher")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Game Server Host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Game Server Port")
    parser.add_argument("--scale", type=float, default=1.0, help="UI Scale Factor")
    return parser.parse_args()

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    args = parse_args()
    
    client = GameClient(host=args.host, port=args.port)
    client.start()
    
    try:
        run_terminal_login(client)
    
        cell_size = int(CELL_SIZE * args.scale)
        geometry = BoardGeometry(cell_size)
        
        asset_loader = AssetLoader(
            piece_size=(cell_size, cell_size),
            board_size=(8 * cell_size, 8 * cell_size)
        )
        logger.info("Loading graphic sprites...")
        asset_loader.load_all()
        
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
        
        screen_manager = ScreenManager()
        
        # Initialize the OnlineCoordinator (configures callbacks and handles state checking)
        coordinator = OnlineCoordinator(
            client=client,
            screen_manager=screen_manager,
            geometry=geometry,
            renderer=renderer,
            animation_manager=animation_manager
        )
        coordinator.setup_screens()
        
        # Initialize the OnlineUIRunner to manage the OpenCV window and game loop execution
        runner = OnlineUIRunner(
            client=client,
            screen_manager=screen_manager,
            window=window,
            coordinator=coordinator,
            time_step_ms=TIME_STEP_MS
        )
        
        runner.start_loop()
                
    finally:
        logger.info("Shutting down online chess client...")
        client.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
