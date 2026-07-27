import logging
from typing import Optional, Tuple, Any
from server.database.postgres_db_manager import PostgresDBManager
from server.services.auth_service import authenticate_user
from shared.constants import DEFAULT_RATING

logger = logging.getLogger("APIGateway.UserService")


class UserService:
    """Service layer encapsulating database access and user/auth business logic for API Gateway."""

    def __init__(self, db_manager: Optional[PostgresDBManager] = None):
        self.db_manager = db_manager or PostgresDBManager()

    def login_user(self, username: str, password: str) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Authenticates user credentials against the database."""
        return authenticate_user(username, password, self.db_manager)

    def get_user_rating(self, username: str) -> int:
        """Fetches rating for a user from database."""
        return self.db_manager.get_user_rating(username)
