import sys
import pathlib
# Add workspace root to path to resolve top-level imports
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

import logging
import argparse
from models.game_state import GameState
from engine.game_engine import GameEngine
from engine.controller import Controller
from services.board_parser import TextBoardParser
from ui.board.board_geometry import BoardGeometry
from ui.assets.asset_loader import AssetLoader
from ui.animation.animation_manager import AnimationManager
from ui.rendering.window import Window
from ui.interaction.mouse_handler import MouseHandler
from ui.rendering.renderer import Renderer
from ui.app.ui_runner import UIRunner
from ui.history.history_tracker import UIHistoryTracker
from constants import DEFAULT_BOARD_LAYOUT

logger = logging.getLogger(__name__)

def parse_board_file(filepath: str):
    """Utility to load a board structure from a text file."""
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Filter out commands section if any
    board_lines = []
    for line in lines:
        if line.startswith("Board:"):
            continue
        board_lines.append(line)
        
    return TextBoardParser().parse(board_lines)

def main():
    # Setup logging configuration
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    parser = argparse.ArgumentParser(description="Kung-Fu Chess GUI Launcher")
    parser.add_argument("--board", type=str, help="Path to board configuration text file", default=None)
    args = parser.parse_args()

    # 1. Parse or initialize board
    if args.board:
        try:
            board = parse_board_file(args.board)
            logger.info(f"Loaded custom board from: {args.board}")
        except Exception as e:
            logger.error(f"Failed to parse custom board file: {e}. Falling back to default chess board.")
            board = TextBoardParser().parse(DEFAULT_BOARD_LAYOUT)
    else:
        board = TextBoardParser().parse(DEFAULT_BOARD_LAYOUT)

    # 2. Initialize Game Engine models
    state = GameState(board=board)
    game_engine = GameEngine()
    controller = Controller(state, game_engine, sys.stdout)

    # 3. Initialize UI elements
    geometry = BoardGeometry()
    
    asset_loader = AssetLoader()
    logger.info("Preloading visual sprites and config assets...")
    asset_loader.load_all()
    logger.info("Assets loaded successfully.")

    animation_manager = AnimationManager(geometry, asset_loader)
    window = Window(title="Kung-Fu Chess")

    left_padding = 250
    right_padding = 250
    history_tracker = UIHistoryTracker()

    mouse_handler = MouseHandler(controller, geometry, left_padding=left_padding)
    renderer = Renderer(
        asset_loader, 
        geometry, 
        history_tracker=history_tracker, 
        left_padding=left_padding, 
        right_padding=right_padding
    )

    # 4. Instantiate and execute the Runner loop
    time_step_ms = 50
    runner = UIRunner(
        controller=controller,
        mouse_handler=mouse_handler,
        renderer=renderer,
        animation_manager=animation_manager,
        window=window,
        time_step_ms=time_step_ms,
        history_tracker=history_tracker
    )

    # Monkeypatch OpenCV to handle automatic ticking with Img.show()
    import cv2
    _original_waitKey = cv2.waitKey
    _original_destroy = cv2.destroyAllWindows

    cv2.waitKey = lambda delay: _original_waitKey(time_step_ms) if delay == 0 else _original_waitKey(delay)
    cv2.destroyAllWindows = lambda: None

    logger.info("Starting Kung-Fu Chess UI Game Loop...")
    try:
        runner.start_loop()
    finally:
        # Revert patches and clean up windows on exit
        cv2.destroyAllWindows = _original_destroy
        cv2.waitKey = _original_waitKey
        _original_destroy()

    logger.info("Application exited successfully.")

if __name__ == "__main__":
    main()
