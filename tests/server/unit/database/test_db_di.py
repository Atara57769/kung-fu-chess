from typing import Optional, Dict
from server.database.base_db_manager import BaseDBManager, User
from server.database.sqlite_db_manager import SQLiteDBManager
from server.services.game_coordinator import GameCoordinator
from server.network.server import GameServer


class MemoryDBForTesting(BaseDBManager):
    """Custom in-memory database implementation for DI testing."""

    def __init__(self) -> None:
        self.users: Dict[str, Dict] = {}

    def get_user_rating(self, username: str) -> int:
        user = self.users.get(username)
        return user["rating"] if user else 1200

    def register_user(self, username: str, password_plain: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = {"password": password_plain, "rating": 1200}
        return True

    def find_user(self, username: str) -> Optional[User]:
        if username not in self.users:
            return None
        u_data = self.users[username]
        return User(username=username, rating=u_data["rating"])

    def verify_password(self, username: str, password_plain: str) -> bool:
        user = self.users.get(username)
        if not user:
            return False
        return user["password"] == password_plain

    def update_user_rating(self, username: str, new_rating: int) -> bool:
        if username not in self.users:
            return False
        self.users[username]["rating"] = new_rating
        return True


def test_sqlite_db_manager_inherits_base():
    """Verify SQLiteDBManager inherits from BaseDBManager."""
    assert issubclass(SQLiteDBManager, BaseDBManager)


def test_game_coordinator_di_custom_db():
    """Verify GameCoordinator accepts a custom injected DB manager."""
    custom_db = MemoryDBForTesting()
    custom_db.register_user("di_user", "pass123")
    
    coordinator = GameCoordinator(db=custom_db)
    assert coordinator.db is custom_db
    
    user = coordinator.db.find_user("di_user")
    assert user is not None
    assert user.username == "di_user"
    assert user.rating == 1200


def test_game_server_di_custom_db():
    """Verify GameServer forwards injected DB manager to coordinator."""
    custom_db = MemoryDBForTesting()
    server = GameServer(db=custom_db)
    
    assert server.coordinator.db is custom_db
