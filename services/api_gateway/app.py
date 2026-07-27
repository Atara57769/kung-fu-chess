import os
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
import redis.asyncio as aioredis

from shared.constants import DEFAULT_RATING, ResponseStatus
from shared.message_contracts.subjects import (MATCHMAKING_REQUEST, ROOM_CREATE)
from shared.message_contracts.contracts import (
    MatchmakingRequestPayload, AuthResponsePayload, MatchmakingResponsePayload,
    RoomListResponsePayload, RoomInfoDTO, HealthStatusPayload,
    AuthRequest, MatchmakingRequest
)
from shared.message_contracts.nats_client import NatsBus
from services.api_gateway.services import UserService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] API Gateway: %(message)s")
logger = logging.getLogger("APIGateway")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

user_service = UserService()
nats_bus = NatsBus(url=NATS_URL)
redis_client: Optional[aioredis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        await nats_bus.connect()
        logger.info("API Gateway NATS connection established.")
    except Exception as e:
        logger.warning("NATS connection not ready on startup: %s", e)
    yield
    await nats_bus.close()
    if redis_client:
        await redis_client.aclose()

app = FastAPI(title="Kung-Fu Chess API Gateway", version="2.0.0", lifespan=lifespan)

@app.get("/healthz", response_model=None)
async def health_check() -> HealthStatusPayload:
    return HealthStatusPayload(status=ResponseStatus.OK.value, service="api_gateway")

@app.post("/auth/login", response_model=None)
async def login(req: AuthRequest) -> AuthResponsePayload:
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password required")

    success, user_info, err_msg = user_service.login_user(req.username, req.password)
    if not success or not user_info:
        raise HTTPException(status_code=401, detail=err_msg or "Authentication failed.")

    token = str(uuid.uuid4())
    if redis_client:
        await redis_client.set(f"session:{token}", user_info.username, ex=86400)

    return AuthResponsePayload(
        status=ResponseStatus.SUCCESS.value,
        username=user_info.username,
        token=token,
        rating=user_info.rating
    )

@app.get("/rooms", response_model=None)
async def list_rooms() -> RoomListResponsePayload:
    if not redis_client:
        return RoomListResponsePayload(rooms=[])
    routes = await redis_client.hgetall("room_routes")
    room_dtos = [RoomInfoDTO(room_id=r_id, shard_id=s_id) for r_id, s_id in routes.items()]
    return RoomListResponsePayload(rooms=room_dtos)


@app.post("/matchmaking/join", response_model=None)
async def join_matchmaking(req: MatchmakingRequest) -> MatchmakingResponsePayload:
    if redis_client:
        session_user = await redis_client.get(f"session:{req.token}")
        if not session_user or session_user != req.username:
            raise HTTPException(status_code=401, detail="Invalid session token")

    rating = user_service.get_user_rating(req.username)
    match_dto = MatchmakingRequestPayload(action="join", username=req.username, rating=rating, token=req.token)

    try:
        await nats_bus.publish(MATCHMAKING_REQUEST, match_dto)
    except Exception as e:
        logger.error("Failed to publish matchmaking request: %s", e)

    return MatchmakingResponsePayload(status=ResponseStatus.QUEUED.value, username=req.username)


@app.post("/matchmaking/leave", response_model=None)
async def leave_matchmaking(req: MatchmakingRequest) -> MatchmakingResponsePayload:
    match_dto = MatchmakingRequestPayload(action="leave", username=req.username, token=req.token)
    try:
        await nats_bus.publish(MATCHMAKING_REQUEST, match_dto)
    except Exception as e:
        logger.error("Failed to publish leave matchmaking request: %s", e)
    return MatchmakingResponsePayload(status=ResponseStatus.REMOVED.value, username=req.username)


@app.get("/history")
async def get_history(username: Optional[str] = None):
    return {"history": []}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("services.api_gateway.app:app", host="0.0.0.0", port=port, reload=False)
