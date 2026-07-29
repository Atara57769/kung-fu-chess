import os
import asyncio
import logging
import uvicorn
from services.observability_service.app import app
from services.observability_service import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ObservabilityService: %(message)s")
logger = logging.getLogger("ObservabilityService")


def main():
    """Service entry point for running the Observability HTTP server."""
    port = int(os.getenv("PORT", str(config.PORT)))
    uv_config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    logger.info("Observability Service starting on http://0.0.0.0:%d", port)
    server = uvicorn.Server(uv_config)
    return server


if __name__ == "__main__":
    server_instance = main()
    asyncio.run(server_instance.serve())
