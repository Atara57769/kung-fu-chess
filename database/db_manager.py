import sqlite3
import hashlib
import os
import logging
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    username: str
    rating: int

logger = logging.getLogger(__name__)

DB_FILE = "kung_fu_chess.db"
DEFAULT_RATING = 1200

class DBManager:
    """Manages SQLite database storage for users, authentication, and ELO ratings."""
    
    def __init__(self, db_path: str = DB_FILE) -> None:
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection context to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def _initialize_db(self) -> None:
        """Creates the users table if it does not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    rating INTEGER DEFAULT 1200
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully.")

    def _hash_password(self, password: str) -> str:
        """Computes a SHA-256 hash of the password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def get_user_rating(self, username: str) -> int:
        """Retrieves the ELO rating for the specified user, returning 1200 if not found."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rating FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row is not None:
                return row[0]
            return DEFAULT_RATING

    def register_user(self, username: str, password_plain: str) -> bool:
        """Inserts a new user record into the database."""
        p_hash = self._hash_password(password_plain)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, rating) VALUES (?, ?, ?)",
                    (username, p_hash, DEFAULT_RATING)
                )
                conn.commit()
                logger.info(f"User '{username}' registered successfully.")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Registration failed: User '{username}' already exists.")
            return False

    def authenticate_or_register(self, username: str, password_plain: str) -> Optional[User]:
        """
        Authenticates user if exists. 
        If user does not exist, registers them automatically as White/Black onboarding helper.
        Returns a User instance if successful, else None.
        """
        p_hash = self._hash_password(password_plain)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, rating FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row is not None:
                db_hash, rating = row
                if db_hash == p_hash:
                    logger.info(f"Authentication successful for '{username}'")
                    return User(
                        username=username,
                        rating=rating
                    )
                else:
                    logger.warning(f"Failed authentication for '{username}': password mismatch.")
                    return None

        logger.info(f"User '{username}' not found. Auto-registering user.")
        success = self.register_user(username, password_plain)
        if success:
            return User(
                username=username,
                rating=DEFAULT_RATING
            )
        return None

    def update_user_rating(self, username: str, new_rating: int) -> bool:
        """Updates the ELO rating for the specified user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET rating = ? WHERE username = ?", (new_rating, username))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Updated rating for '{username}' to {new_rating}.")
                return True
            logger.warning(f"Could not update rating: User '{username}' does not exist.")
            return False
