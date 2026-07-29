import argparse
import asyncio
import logging
from server.network.server import GameServer
from server.database.sqlite_db_manager import SQLiteDBManager
from shared.constants import DEFAULT_HOST, DEFAULT_PORT

def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments for hosting the chess server."""
    parser = argparse.ArgumentParser(description="Kung-Fu Chess WebSocket Server")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host address to bind to")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL/TLS encryption")
    parser.add_argument("--ssl-cert", type=str, default=None, help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", type=str, default=None, help="Path to SSL private key file")
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
    
    db = SQLiteDBManager()
    server = GameServer(
        host=args.host,
        port=args.port,
        db=db,
        use_ssl=not args.no_ssl,
        ssl_cert=args.ssl_cert,
        ssl_key=args.ssl_key,
    )
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.info("Server shut down by user.")

if __name__ == "__main__":
    main()
