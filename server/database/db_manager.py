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
            logger.info("Database initialized successfully.")

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
                logger.info("User '%s' registered successfully.", username)
                return True
        except sqlite3.IntegrityError:
            logger.warning("Registration failed: User '%s' already exists.", username)
            return False

    def find_user(self, username: str) -> Optional[User]:
        """Looks up a user by username. Returns a User if found, else None."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SQL_SELECT_AUTH, (username,))
            row = cursor.fetchone()
        if row is None:
            return None
        _, rating = row
        return User(username=username, rating=rating)

    def verify_password(self, username: str, password_plain: str) -> bool:
        """Checks whether the given password matches the stored hash for username."""
        p_hash = self._hash_password(password_plain)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SQL_SELECT_AUTH, (username,))
            row = cursor.fetchone()
        if row is None:
            return False
        db_hash, _ = row
        return db_hash == p_hash

    def update_user_rating(self, username: str, new_rating: int) -> bool:
        """Updates the ELO rating for the specified user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SQL_UPDATE_RATING, (new_rating, username))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info("Updated rating for '%s' to %d.", username, new_rating)
                return True
            logger.warning("Could not update rating: User '%s' does not exist.", username)
            return False
