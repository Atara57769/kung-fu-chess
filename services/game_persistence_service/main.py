import asyncio
from services.game_persistence_service.app import main as run_persistence_service


if __name__ == "__main__":
    asyncio.run(run_persistence_service())
