import logging
from websockets.exceptions import ConnectionClosed
from server.network.models import ConnectedPlayer

logger = logging.getLogger(__name__)

async def client_connection(websocket, server_instance) -> None:
    """Entry handler for each new WebSocket connection client."""
    ip = websocket.remote_address[0]
    player = ConnectedPlayer(websocket, ip)
    server_instance.players[websocket] = player
    logger.info(f"Connection opened from {ip}")
    
    try:
        async for message in websocket:
            await server_instance.dispatch_message(player, message)
    except ConnectionClosed:
        logger.info(f"Connection closed by client {ip}")
    finally:
        await server_instance.handle_disconnect(player)
        if websocket in server_instance.players:
            del server_instance.players[websocket]
