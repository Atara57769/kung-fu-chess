import os

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
PORT = int(os.getenv("PORT", "8001"))
GATEWAY_ID = os.getenv("GATEWAY_ID", "ws_gw_1")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
