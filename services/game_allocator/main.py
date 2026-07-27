import asyncio
from services.game_allocator.app import main as run_game_allocator


if __name__ == "__main__":
    asyncio.run(run_game_allocator())
