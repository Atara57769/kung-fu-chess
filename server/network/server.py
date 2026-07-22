from dataclasses import is_dataclass, asdict
import asyncio
import json
import logging
from typing import Dict
import websockets
from websockets.exceptions import ConnectionClosed
from shared.constants import DEFAULT_HOST, DEFAULT_PORT
from server.network.models import ConnectedPlayer
from server.services.game_coordinator import GameCoordinator

logger = logging.getLogger(__name__)


class GameServer:
    """WebSocket server coordinating network connection sessions and message passing."""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str = None) -> None:
        self.host = host
        self.port = port
        self.coordinator = GameCoordinator(db_path)
        self.coordinator.set_send_json_fn(self._send_json)
        self.players: Dict[any, ConnectedPlayer] = {}

    async def start(self) -> None:
        """Starts the WebSocket server listening loop."""
        async with websockets.serve(self.handle_client_connection, self.host, self.port):
            logger.info(f"Kung-Fu Chess Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()

    async def handle_client_connection(self, websocket, path=None) -> None:
        """Entry handler for each new WebSocket connection client."""
        ip = websocket.remote_address[0]
        player = ConnectedPlayer(websocket, ip)
        self.players[websocket] = player
        logger.info(f"Connection opened from {ip}")
        
        try:
            async for message in websocket:
                await self.coordinator.dispatch_message(player, message)
        except ConnectionClosed:
            logger.info(f"Connection closed by client {ip}")
        finally:
            await self.coordinator.handle_disconnect(player)
            if websocket in self.players:
                del self.players[websocket]

    async def _send_json(self, ws, data: any) -> None:
        """Utility to safely send a JSON string to a WebSocket client."""
        if is_dataclass(data):
            data = asdict(data)
        try:
            await ws.send(json.dumps(data))
        except ConnectionClosed:
            pass
