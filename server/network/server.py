import asyncio
import logging
import ssl
from typing import Dict, Tuple, Optional
import websockets
from websockets.exceptions import ConnectionClosed
from shared.constants import DEFAULT_HOST, DEFAULT_PORT
from shared.protocol import serialize_message
from shared.security.ssl_config import get_server_ssl_context
from server.network.models import ConnectedPlayer
from server.services.game_coordinator import GameCoordinator
from server.database.base_db_manager import BaseDBManager

logger = logging.getLogger(__name__)


class GameServer:
    """WebSocket server coordinating network connection sessions and message passing.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        db: Optional[BaseDBManager] = None,
        use_ssl: bool = True,
        ssl_cert: Optional[str] = None,
        ssl_key: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.coordinator = GameCoordinator(db=db)
        self.coordinator.set_send(self._send_json)
        self.players: Dict[any, ConnectedPlayer] = {}
        self._message_queue: asyncio.Queue[Tuple[ConnectedPlayer, str]] = asyncio.Queue()
        self.use_ssl = use_ssl

        if use_ssl:
            if ssl_context is not None:
                self.ssl_context = ssl_context
            else:
                self.ssl_context = get_server_ssl_context(cert_path=ssl_cert, key_path=ssl_key, auto_generate=True)
        else:
            self.ssl_context = None

    async def start(self) -> None:
        """Starts the message-worker and WebSocket listening loop."""
        worker_task = asyncio.create_task(self._message_worker())
        scheme = "wss" if self.ssl_context else "ws"
        try:
            async with websockets.serve(self.handle_client_connection, self.host, self.port, ssl=self.ssl_context):
                logger.info(f"Kung-Fu Chess Server started on {scheme}://{self.host}:{self.port}")
                await asyncio.Future()
        finally:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

    async def _message_worker(self) -> None:
        """Single coroutine that drains the message queue one item at a time.
        """
        logger.info("Message queue worker started.")
        try:
            while True:
                player, raw_msg = await self._message_queue.get()
                try:
                    await self.coordinator.dispatch_message(player, raw_msg)
                except Exception:
                    logger.exception("Unhandled error dispatching queued message.")
                finally:
                    self._message_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Message queue worker stopped.")

    async def handle_client_connection(self, websocket, path=None) -> None:
        """Entry handler for each new WebSocket connection client.
        """
        ip = websocket.remote_address[0]
        player = ConnectedPlayer(websocket, ip)
        self.players[websocket] = player
        logger.info(f"Connection opened from {ip}")

        try:
            async for message in websocket:
                await self._message_queue.put((player, message))
        except ConnectionClosed:
            logger.info(f"Connection closed by client {ip}")
        finally:
            await self.coordinator.handle_disconnect(player)
            if websocket in self.players:
                del self.players[websocket]

    async def _send_json(self, ws, data: any) -> None:
        """Utility to safely send a serialized message string to a WebSocket client."""
        try:
            await ws.send(serialize_message(data))
        except ConnectionClosed:
            pass

