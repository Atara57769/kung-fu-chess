import argparse
import sys
import logging
import time
import cv2

from shared.constants import DEFAULT_HOST, CELL_SIZE, ResponseStatus
from client.ui.ui_config import LEFT_PADDING, RIGHT_PADDING, TIME_STEP_MS
from client.ui.board.board_geometry import BoardGeometry
from client.ui.assets.asset_loader import AssetLoader
from client.ui.animation.animation_manager import AnimationManager
from client.ui.rendering.window import Window
from client.ui.rendering.game_renderer import GameRenderer
from client.ui.history.history_tracker import UIHistoryTracker
from client.services.score_tracker import ScoreTracker
from client.ui.screens.screen_manager import ScreenManager
from client.network.distributed_client import DistributedGameClient
from client.ui.app.terminal_login import prompt_terminal_credentials
from client.ui.app.online_coordinator import OnlineCoordinator
from client.ui.app.online_runner import OnlineUIRunner

logger = logging.getLogger("DistributedClient")


def parse_args(args=None) -> argparse.Namespace:
    """Parses launcher parameters for the distributed client."""
    parser = argparse.ArgumentParser(description="Kung-Fu Chess Distributed Client Launcher")
    parser.add_argument("--api-host", type=str, default="http://localhost:8000", help="API Gateway URL")
    parser.add_argument("--ws-host", type=str, default="localhost", help="WebSocket Gateway Host")
    parser.add_argument("--ws-port", type=int, default=8001, help="WebSocket Gateway Port")
    parser.add_argument("--scale", type=float, default=1.0, help="UI Scale Factor")
    return parser.parse_args(args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    args = parse_args()

    client = DistributedGameClient(api_url=args.api_host, ws_host=args.ws_host, ws_port=args.ws_port)

    username, password = prompt_terminal_credentials()
    print("\nAuthenticating via API Gateway REST Endpoint...")
    res = client.api_login(username, password)
    if res.status == ResponseStatus.SUCCESS.value:
        print(f"Authentication success! Welcome {client.username} (ELO: {client.rating})\n")
    else:
        print(f"Authentication failed for user '{username}'")
        sys.exit(1)

    # Step 2: Start WebSocket thread and send WS auth message
    client.start()
    client.authenticate(client.username, client.token)

    start_t = time.time()
    while not client.authenticated and not client.error_message:
        time.sleep(0.1)
        if time.time() - start_t > 5.0:
            client.authenticated = True
            break

    if client.error_message:
        print(f"WebSocket session authentication failed: {client.error_message}")
        client.stop()
        sys.exit(1)

    try:
        cell_size = int(CELL_SIZE * args.scale)
        geometry = BoardGeometry(cell_size)

        asset_loader = AssetLoader(
            piece_size=(cell_size, cell_size),
            board_size=(8 * cell_size, 8 * cell_size)
        )
        logger.info("Loading graphic sprites...")
        asset_loader.load_all()

        score_tracker = ScoreTracker(client.pubsub)
        history_tracker = UIHistoryTracker()

        animation_manager = AnimationManager(geometry, asset_loader)
        window = Window(title=f"Kung-Fu Chess (Distributed): {client.username}")

        renderer = GameRenderer(
            asset_loader,
            geometry,
            history_tracker=history_tracker,
            left_padding=LEFT_PADDING,
            right_padding=RIGHT_PADDING,
            score_tracker=score_tracker
        )

        screen_manager = ScreenManager()

        coordinator = OnlineCoordinator(
            client=client,
            screen_manager=screen_manager,
            geometry=geometry,
            renderer=renderer,
            animation_manager=animation_manager
        )
        coordinator.setup_screens()

        runner = OnlineUIRunner(
            client=client,
            screen_manager=screen_manager,
            window=window,
            coordinator=coordinator,
            time_step_ms=TIME_STEP_MS
        )

        runner.start_loop()

    except KeyboardInterrupt:
        logger.info("Client terminated by user.")
    finally:
        client.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
