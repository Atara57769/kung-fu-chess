import os

PORT = int(os.getenv("PORT", "8002"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "kung_fu_chess")

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
WS_GATEWAY_URL = os.getenv("WS_GATEWAY_URL", "http://localhost:8001")

MAX_LOG_ENTRIES = int(os.getenv("MAX_LOG_ENTRIES", "10000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
