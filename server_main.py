import argparse
import asyncio
import logging
from network.server import GameServer
from constants import DEFAULT_HOST, DEFAULT_PORT

def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments for hosting the chess server."""
    parser = argparse.ArgumentParser(description="Kung-Fu Chess WebSocket Server")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host address to bind to")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    return parser.parse_args()

def configure_logging() -> None:
    """Sets up standard output logging format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

def main() -> None:
    """Starts the game server and runs the event loop."""
    configure_logging()
    args = parse_arguments()
    
    server = GameServer(host=args.host, port=args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.info("Server shut down by user.")

if __name__ == "__main__":
    main()
