import logging
from server.network.models import ConnectedPlayer
from shared.protocol import AuthMessage, AuthResponseMessage

logger = logging.getLogger(__name__)

# Constants
ERROR_INVALID_FIELDS = "Invalid fields."
ERROR_AUTH_FAILED = "Authentication failed."

async def handle_auth(player: ConnectedPlayer, msg: AuthMessage, db, send_json_fn) -> None:
    """Verifies credentials against DBManager and updates player session."""
    username = msg.username.strip()
    password = msg.password.strip()
    
    if not username or not password:
        await send_json_fn(player.ws, AuthResponseMessage(success=False, error=ERROR_INVALID_FIELDS))
        return

    user_info = db.authenticate_or_register(username, password)
    if user_info:
        player.username = user_info.username
        player.rating = user_info.rating
        player.authenticated = True
        await send_json_fn(player.ws, AuthResponseMessage(
            success=True,
            username=player.username,
            rating=player.rating
        ))
        logger.info(f"Player {player.username} authenticated successfully.")
    else:
        await send_json_fn(player.ws, AuthResponseMessage(
            success=False,
            error=ERROR_AUTH_FAILED
        ))



