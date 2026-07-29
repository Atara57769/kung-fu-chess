import logging
from typing import Tuple, Optional
from server.network.models import ConnectedPlayer
from server.database.base_db_manager import DEFAULT_RATING, User, BaseDBManager
from shared.constants import ResponseStatus
from shared.protocol import AuthMessage, AuthResponseMessage
from server.services.server_event_bus import ServerEventType

logger = logging.getLogger(__name__)

# Constants
ERROR_INVALID_FIELDS = "Invalid fields."
ERROR_AUTH_FAILED = "Authentication failed."


def authenticate_user(username: str, password_plain: str, db: BaseDBManager) -> Tuple[bool, Optional[User], str]:
    """Core auth function: Checks if user exists.
    - If user exists: verifies password.
    - If user does not exist: auto-registers new user.
    """
    username = username.strip()
    password = password_plain.strip()

    if not username or not password:
        return False, None, ERROR_INVALID_FIELDS

    user_info = db.find_user(username)

    if user_info is None:
        logger.info("User '%s' not found. Auto-registering.", username)
        registered = db.register_user(username, password)
        if registered:
            user_info = User(username=username, rating=DEFAULT_RATING)
        else:
            logger.warning("Auto-registration failed for '%s'.", username)
            return False, None, ERROR_AUTH_FAILED
    elif not db.verify_password(username, password):
        logger.warning("Failed authentication for '%s': password mismatch.", username)
        return False, None, ERROR_AUTH_FAILED

    return True, user_info, ResponseStatus.SUCCESS


async def handle_auth(player: ConnectedPlayer, msg: AuthMessage, db: BaseDBManager, event_bus=None) -> None:
    """Authenticates an existing user or auto-registers a new one, then updates the player session."""
    success, user_info, err_msg = authenticate_user(msg.username, msg.password, db)
    if not success or not user_info:
        response_msg = AuthResponseMessage(success=False, error=err_msg)
        if event_bus:
            await event_bus.publish(ServerEventType.AUTH_RESPONSE, target=player, data=response_msg)
        return

    player.username = user_info.username
    player.rating = user_info.rating
    player.authenticated = True
    response_msg = AuthResponseMessage(
        success=True,
        username=player.username,
        rating=player.rating
    )
    if event_bus:
        await event_bus.publish(ServerEventType.AUTH_RESPONSE, target=player, data=response_msg)
    logger.info(f"Player {player.username} authenticated successfully.")
