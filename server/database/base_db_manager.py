from abc import ABC, abstractmethod
import os
from typing import Optional
from dataclasses import dataclass
from shared.constants import DEFAULT_RATING


@dataclass(frozen=True)
class User:
    username: str
    rating: int


DB_NAME = "kung_fu_chess.db"
DB_FILE = os.path.join(os.path.dirname(__file__), DB_NAME)
ENCODING_UTF8 = "utf-8"


class BaseDBManager(ABC):
    """Abstract base class interface for database management."""

    @abstractmethod
    def get_user_rating(self, username: str) -> int:
        """Retrieves the ELO rating for the specified user."""
        pass

    @abstractmethod
    def register_user(self, username: str, password_plain: str) -> bool:
        """Inserts a new user record into the database."""
        pass

    @abstractmethod
    def find_user(self, username: str) -> Optional[User]:
        """Looks up a user by username. Returns a User if found, else None."""
        pass

    @abstractmethod
    def verify_password(self, username: str, password_plain: str) -> bool:
        """Checks whether the given password matches the stored credential."""
        pass

    @abstractmethod
    def update_user_rating(self, username: str, new_rating: int) -> bool:
        """Updates the ELO rating for the specified user."""
        pass
