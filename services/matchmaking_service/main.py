import asyncio
from services.matchmaking_service.app import main as run_matchmaking_service


if __name__ == "__main__":
    asyncio.run(run_matchmaking_service())
