import os
import asyncio
import logging
import uvicorn
from services.api_gateway.app import app
from shared.security.ssl_config import generate_self_signed_cert

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] API Gateway: %(message)s")
logger = logging.getLogger("APIGateway")


async def main():
    port = int(os.getenv("PORT", "8000"))
    use_ssl = os.getenv("USE_SSL", "true").lower() not in ("false", "0", "no", "off")

    ssl_cert = os.getenv("SSL_CERT_FILE")
    ssl_key = os.getenv("SSL_KEY_FILE")

    if use_ssl:
        if not ssl_cert or not ssl_key:
            ssl_cert, ssl_key = generate_self_signed_cert()
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            ssl_certfile=ssl_cert,
            ssl_keyfile=ssl_key
        )
        logger.info("API Gateway starting on https://0.0.0.0:%d", port)
    else:
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        logger.info("API Gateway starting on http://0.0.0.0:%d", port)

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
