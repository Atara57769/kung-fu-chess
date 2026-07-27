import asyncio
from services.rooms_service.app import main as run_rooms_service


if __name__ == "__main__":
    asyncio.run(run_rooms_service())
