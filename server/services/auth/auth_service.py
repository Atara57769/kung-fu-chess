import logging
from server.network.models import ConnectedPlayer
from server.database.db_manager import DEFAULT_RATING, User
from shared.protocol import AuthMessage, AuthResponseMessage

logger = logging.getLogger(__name__)

# Constants
ERROR_INVALID_FIELDS = "Invalid fields."
ERROR_AUTH_FAILED = "Authentication failed."

async def handle_auth(player: ConnectedPlayer, msg: AuthMessage, db, send) -> None:
    """Authenticates an existing user or auto-registers a new one, then updates the player session."""
    username = msg.username.strip()
    password = msg.password.strip()

    if not username or not password:
        await send(player.ws, AuthResponseMessage(success=False, error=ERROR_INVALID_FIELDS))
        return

    user_info = db.find_user(username)

    if user_info is None:
        logger.info("User '%s' not found. Auto-registering.", username)
        registered = db.register_user(username, password)
        if registered:
            user_info = User(username=username, rating=DEFAULT_RATING)
        else:
            logger.warning("Auto-registration failed for '%s'.", username)
    elif not db.verify_password(username, password):
        logger.warning("Failed authentication for '%s': password mismatch.", username)
        await send(player.ws, AuthResponseMessage(success=False, error=ERROR_AUTH_FAILED))
        return

    if user_info:
        player.username = user_info.username
        player.rating = user_info.rating
        player.authenticated = True
        await send(player.ws, AuthResponseMessage(
            success=True,
            username=player.username,
            rating=player.rating
        ))
        logger.info(f"Player {player.username} authenticated successfully.")
    else:
        await send(player.ws, AuthResponseMessage(success=False, error=ERROR_AUTH_FAILED))



