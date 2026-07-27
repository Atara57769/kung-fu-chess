import os
import logging
from typing import Optional
from server.database.sqlite_db_manager import SQLiteDBManager, Base, UserModel
from server.database.base_db_manager import DEFAULT_RATING

logger = logging.getLogger(__name__)


class PostgresDBManager(SQLiteDBManager):
    """Database manager for PostgreSQL using SQLAlchemy ORM.
    Reads host, port, user, password, and database name from environment variables.
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                host = os.getenv("POSTGRES_HOST", "postgres")
                port = os.getenv("POSTGRES_PORT", "5432")
                user = os.getenv("POSTGRES_USER", "postgres")
                password = os.getenv("POSTGRES_PASSWORD", "postgres")
                dbname = os.getenv("POSTGRES_DB", "kung_fu_chess")
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        
        logger.info("Initializing PostgresDBManager with URL: %s", database_url)
        super().__init__(db_path=database_url)
