import os
import asyncio
import logging
from typing import Optional

from shared.message_contracts.subjects import GAME_FINISHED
from shared.message_contracts.contracts import GameFinishedPayload
from shared.message_contracts.nats_client import NatsBus
from server.database.postgres_db_manager import PostgresDBManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] GamePersistenceService: %(message)s"
)
logger = logging.getLogger("GamePersistenceService")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

db_manager = PostgresDBManager()
nats_bus = NatsBus(url=NATS_URL)


async def handle_game_finished(data: GameFinishedPayload, reply_to: Optional[str] = None) -> None:
    """NATS subscriber callback for GAME_FINISHED topic. Saves game results into PostgreSQL."""
    room_id = data.room_id
    if not room_id:
        logger.warning("Received GAME_FINISHED event without room_id: %s", data)
        return

    logger.info(
        "Processing GAME_FINISHED event for room '%s' (winner: %s, reason: %s)",
        room_id, data.winner, data.reason
    )

    success = db_manager.save_game_history(
        room_id=room_id,
        winner=data.winner,
        reason=data.reason,
        final_ratings=data.final_ratings
    )

    if success:
        logger.info("Successfully persisted game record for room '%s' to database.", room_id)
    else:
        logger.error("Failed to persist game record for room '%s' to database.", room_id)


async def main() -> None:
    """Initializes NATS connection and subscribes to GAME_FINISHED events."""
    await nats_bus.connect()
    logger.info("Game Persistence Service online. Subscribing to '%s'...", GAME_FINISHED)
    await nats_bus.subscribe(GAME_FINISHED, handle_game_finished, dto_class=GameFinishedPayload)

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Game Persistence Service shutting down.")

