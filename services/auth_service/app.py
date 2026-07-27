import os
import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional

from shared.constants import DEFAULT_RATING
from shared.message_contracts.subjects import AUTH_LOGIN, AUTH_REGISTER, AUTH_RESULT
from shared.message_contracts.contracts import AuthResultPayload
from shared.message_contracts.nats_client import NatsBus
from server.database.sqlite_db_manager import SQLiteDBManager
from server.database.postgres_db_manager import PostgresDBManager
from server.services.auth_service import authenticate_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Auth Service: %(message)s")
logger = logging.getLogger("AuthService")

db_manager = PostgresDBManager()
nats_bus = NatsBus(url=os.getenv("NATS_URL", "nats://localhost:4222"))


async def handle_auth_login(data: Dict[str, Any], reply_to: Optional[str]) -> Optional[AuthResultPayload]:
    """Handles NATS auth.login request and returns AuthResultPayload DTO."""
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    logger.info("Processing auth.login for user: %s", username)
    success, user_info, err_msg = authenticate_user(username, password, db_manager)

    if success and user_info:
        token = str(uuid.uuid4())
        response = AuthResultPayload(
            success=True,
            username=user_info.username,
            rating=user_info.rating,
            token=token,
            error=None
        )
    else:
        response = AuthResultPayload(
            success=False,
            username=username,
            rating=DEFAULT_RATING,
            token=None,
            error=err_msg or "Authentication failed."
        )

    await nats_bus.publish(AUTH_RESULT, response)
    return response


async def handle_auth_register(data: Dict[str, Any], reply_to: Optional[str]) -> Optional[AuthResultPayload]:
    """Handles NATS auth.register request."""
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        response = AuthResultPayload(success=False, error="Username and password are required")
    else:
        created = db_manager.register_user(username, password)
        if created:
            user_info = db_manager.find_user(username)
            rating = user_info.rating if user_info else DEFAULT_RATING
            token = str(uuid.uuid4())
            response = AuthResultPayload(success=True, username=username, rating=rating, token=token)
        else:
            response = AuthResultPayload(success=False, error="Username already exists")

    await nats_bus.publish(AUTH_RESULT, response)
    return response


async def main():
    await nats_bus.connect()
    logger.info("Auth Service initialized. Subscribing to auth subjects...")
    await nats_bus.subscribe(AUTH_LOGIN, handle_auth_login)
    await nats_bus.subscribe(AUTH_REGISTER, handle_auth_register)
    
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Auth Service shutting down.")
