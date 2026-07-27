import os
import asyncio
import logging
import uvicorn
from services.api_gateway.app import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] API Gateway: %(message)s")
logger = logging.getLogger("APIGateway")


async def main():
    port = int(os.getenv("PORT", "8000"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info("API Gateway starting on http://0.0.0.0:%d", port)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
