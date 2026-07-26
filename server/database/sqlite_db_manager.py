import hashlib
import logging
import os
from typing import Optional

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from server.database.base_db_manager import (
    BaseDBManager, User, DB_FILE, DEFAULT_RATING, ENCODING_UTF8
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy ORM model for user accounts and ratings."""
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    rating = Column(Integer, default=DEFAULT_RATING)


class SQLiteDBManager(BaseDBManager):
    """Manages database storage for users, authentication, and ELO ratings using SQLAlchemy ORM."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.getenv("DATABASE_URL", DB_FILE)
            
        self.db_path = db_path
        if "://" in db_path:
            db_url = db_path
        else:
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
        self.SessionFactory = sessionmaker(bind=self.engine)
        self._initialize_db()


    def _initialize_db(self) -> None:
        """Creates database tables defined in SQLAlchemy ORM models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized successfully with SQLAlchemy ORM.")

    def _hash_password(self, password: str) -> str:
        """Computes a SHA-256 hash of the password."""
        return hashlib.sha256(password.encode(ENCODING_UTF8)).hexdigest()

    def _get_session(self) -> Session:
        """Returns a new SQLAlchemy session context."""
        return self.SessionFactory()

    def get_user_rating(self, username: str) -> int:
        """Retrieves the ELO rating for the specified user, returning DEFAULT_RATING if not found."""
        with self._get_session() as session:
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if user is not None:
                return user.rating
            return DEFAULT_RATING

    def register_user(self, username: str, password_plain: str) -> bool:
        """Inserts a new user record into the database via ORM."""
        p_hash = self._hash_password(password_plain)
        new_user = UserModel(username=username, password_hash=p_hash, rating=DEFAULT_RATING)
        with self._get_session() as session:
            try:
                session.add(new_user)
                session.commit()
                logger.info("User '%s' registered successfully via ORM.", username)
                return True
            except IntegrityError:
                session.rollback()
                logger.warning("Registration failed: User '%s' already exists.", username)
                return False

    def find_user(self, username: str) -> Optional[User]:
        """Looks up a user by username. Returns a User if found, else None."""
        with self._get_session() as session:
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if user is None:
                return None
            return User(username=user.username, rating=user.rating)

    def verify_password(self, username: str, password_plain: str) -> bool:
        """Checks whether the given password matches the stored hash for username."""
        p_hash = self._hash_password(password_plain)
        with self._get_session() as session:
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if user is None:
                return False
            return user.password_hash == p_hash

    def update_user_rating(self, username: str, new_rating: int) -> bool:
        """Updates the ELO rating for the specified user via ORM."""
        with self._get_session() as session:
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if user is not None:
                user.rating = new_rating
                session.commit()
                logger.info("Updated rating for '%s' to %d via ORM.", username, new_rating)
                return True
            logger.warning("Could not update rating: User '%s' does not exist.", username)
            return False


