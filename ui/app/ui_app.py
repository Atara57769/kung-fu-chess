import sys
import pathlib
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
from constants import DEFAULT_BOARD_LAYOUT, CELL_SIZE
from ui.ui_config import LEFT_PADDING, RIGHT_PADDING, TIME_STEP_MS
from core.events import EventBus
from services.score_tracker import ScoreTracker
from services.move_logger import MoveLogger
from services.sound_manager import SoundManager



logger = logging.getLogger(__name__)

def parse_board_file(filepath: str):
    """Utility to load a board structure from a text file."""
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    board_lines = []
    for line in lines:
        if line.startswith("Board:"):
            continue
        board_lines.append(line)
        
    return TextBoardParser().parse(board_lines)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    parser = argparse.ArgumentParser(description="Kung-Fu Chess GUI Launcher")
    parser.add_argument("--board", type=str, help="Path to board configuration text file", default=None)
    parser.add_argument("--scale", type=float, help="Scale factor for the board UI (e.g., 0.5, 1.5)", default=1.0)
    parser.add_argument("--cell-size", type=int, help="Override cell size in pixels directly", default=None)
    args = parser.parse_args()

    if args.board:
        try:
            board = parse_board_file(args.board)
            logger.info(f"Loaded custom board from: {args.board}")
        except Exception as e:
            logger.error(f"Failed to parse custom board file: {e}. Falling back to default chess board.")
            board = TextBoardParser().parse(DEFAULT_BOARD_LAYOUT)
    else:
        board = TextBoardParser().parse(DEFAULT_BOARD_LAYOUT)

    event_bus = EventBus()
    score_tracker = ScoreTracker(event_bus)
    move_logger = MoveLogger(event_bus)
    sound_manager = SoundManager(event_bus)

    state = GameState(board=board)
    game_engine = GameEngine(event_bus=event_bus)
    controller = Controller(state, game_engine, sys.stdout, event_bus=event_bus)

    if args.cell_size is not None:
        cell_size = args.cell_size
    else:
        cell_size = int(CELL_SIZE * args.scale)

    geometry = BoardGeometry(cell_size)
    
    asset_loader = AssetLoader(
        piece_size=(cell_size, cell_size),
        board_size=(board.width * cell_size, board.height * cell_size)
    )
    logger.info("Preloading visual sprites and config assets...")
    asset_loader.load_all()
    logger.info("Assets loaded successfully.")

    animation_manager = AnimationManager(geometry, asset_loader)
    window = Window(title="Kung-Fu Chess")

    left_padding = LEFT_PADDING
    right_padding = RIGHT_PADDING
    history_tracker = UIHistoryTracker()

    mouse_handler = MouseHandler(controller, geometry, left_padding=left_padding)
    renderer = Renderer(
        asset_loader, 
        geometry, 
        history_tracker=history_tracker, 
        left_padding=left_padding, 
        right_padding=right_padding,
        score_tracker=score_tracker
    )

    time_step_ms = TIME_STEP_MS
    runner = UIRunner(
        controller=controller,
        mouse_handler=mouse_handler,
        renderer=renderer,
        animation_manager=animation_manager,
        window=window,
        time_step_ms=time_step_ms,
        history_tracker=history_tracker
    )

    logger.info("Starting Kung-Fu Chess UI Game Loop...")
    try:
        runner.start_loop()
    finally:
        window.close()

    logger.info("Application exited successfully.")

if __name__ == "__main__":
    main()
