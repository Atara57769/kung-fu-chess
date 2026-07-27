import asyncio
from services.websocket_gateway.app import main as run_ws_gateway


if __name__ == "__main__":
    asyncio.run(run_ws_gateway())
