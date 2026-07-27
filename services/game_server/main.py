import asyncio
from services.game_server.app import main as run_game_server


if __name__ == "__main__":
    asyncio.run(run_game_server())
