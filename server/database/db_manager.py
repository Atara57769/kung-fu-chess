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

DB_NAME = "kung_fu_chess.db"
DB_FILE = os.path.join(os.path.dirname(__file__), DB_NAME)
DEFAULT_RATING = 1200
ENCODING_UTF8 = "utf-8"

# SQL Queries
SQL_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        rating INTEGER DEFAULT 1200
    )
"""
SQL_SELECT_RATING = "SELECT rating FROM users WHERE username = ?"
SQL_INSERT_USER = "INSERT INTO users (username, password_hash, rating) VALUES (?, ?, ?)"
SQL_SELECT_AUTH = "SELECT password_hash, rating FROM users WHERE username = ?"
SQL_UPDATE_RATING = "UPDATE users SET rating = ? WHERE username = ?"

LOG_DB_INITIALIZED = "Database initialized successfully."
LOG_REGISTRATION_SUCCESS = "User '%s' registered successfully."
LOG_REGISTRATION_FAILED = "Registration failed: User '%s' already exists."
LOG_AUTH_SUCCESS = "Authentication successful for '%s'"
LOG_AUTH_FAILED = "Failed authentication for '%s': password mismatch."
LOG_USER_NOT_FOUND = "User '%s' not found. Auto-registering user."
LOG_RATING_UPDATED = "Updated rating for '%s' to %d."
LOG_RATING_UPDATE_FAILED = "Could not update rating: User '%s' does not exist."

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
            cursor.execute(SQL_CREATE_TABLE)
            conn.commit()
            logger.info(LOG_DB_INITIALIZED)

    def _hash_password(self, password: str) -> str:
        """Computes a SHA-256 hash of the password."""
        return hashlib.sha256(password.encode(ENCODING_UTF8)).hexdigest()

    def get_user_rating(self, username: str) -> int:
        """Retrieves the ELO rating for the specified user, returning 1200 if not found."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SQL_SELECT_RATING, (username,))
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
                cursor.execute(SQL_INSERT_USER, (username, p_hash, DEFAULT_RATING))
                conn.commit()
                logger.info(LOG_REGISTRATION_SUCCESS, username)
                return True
        except sqlite3.IntegrityError:
            logger.warning(LOG_REGISTRATION_FAILED, username)
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
            cursor.execute(SQL_SELECT_AUTH, (username,))
            row = cursor.fetchone()
            
            if row is not None:
                db_hash, rating = row
                if db_hash == p_hash:
                    logger.info(LOG_AUTH_SUCCESS, username)
                    return User(
                        username=username,
                        rating=rating
                    )
                else:
                    logger.warning(LOG_AUTH_FAILED, username)
                    return None

        logger.info(LOG_USER_NOT_FOUND, username)
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
            cursor.execute(SQL_UPDATE_RATING, (new_rating, username))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(LOG_RATING_UPDATED, username, new_rating)
                return True
            logger.warning(LOG_RATING_UPDATE_FAILED, username)
            return False
