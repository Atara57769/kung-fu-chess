import os

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
GAME_SERVERS = os.getenv("GAME_SERVERS", "game_server_1,game_server_2").split(",")
