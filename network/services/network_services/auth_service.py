import logging
from network.models import ConnectedPlayer

logger = logging.getLogger(__name__)

async def handle_auth(player: ConnectedPlayer, data: dict, db, send_json_fn) -> None:
    """Verifies credentials against DBManager and updates player session."""
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        await send_json_fn(player.ws, {"type": "auth_response", "success": False, "error": "Invalid fields."})
        return

    user_info = db.authenticate_or_register(username, password)
    if user_info:
        player.username = user_info["username"]
        player.rating = user_info["rating"]
        player.authenticated = True
        await send_json_fn(player.ws, {
            "type": "auth_response",
            "success": True,
            "username": player.username,
            "rating": player.rating
        })
        logger.info(f"Player {player.username} authenticated successfully.")
    else:
        await send_json_fn(player.ws, {
            "type": "auth_response",
            "success": False,
            "error": "Authentication failed."
        })
