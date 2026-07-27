import asyncio
from services.auth_service.app import main as run_auth_service


if __name__ == "__main__":
    asyncio.run(run_auth_service())
