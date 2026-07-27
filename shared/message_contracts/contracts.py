"""
Data Transfer Objects (DTOs) and Message Contracts for NATS Event Bus and API Responses.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from shared.constants import DEFAULT_RATING


@dataclass
class AuthLoginPayload:
    username: str
    password: Optional[str] = None
    token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuthResultPayload:
    success: bool
    username: Optional[str] = None
    token: Optional[str] = None
    rating: int = DEFAULT_RATING
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuthResponsePayload:
    status: str
    username: str
    token: Optional[str] = None
    rating: int = DEFAULT_RATING

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchmakingRequestPayload:
    action: str  # "join" or "leave"
    username: str
    rating: int = DEFAULT_RATING
    token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchmakingResponsePayload:
    status: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchFoundPayload:
    match_id: str
    room_id: str
    player1: str
    player2: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomCreatePayload:
    room_id: str
    host: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomCreatedPayload:
    room_id: str
    host: str
    created_at: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomJoinPayload:
    room_id: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomLeavePayload:
    room_id: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomInfoDTO:
    room_id: str
    shard_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomListResponsePayload:
    rooms: List[RoomInfoDTO]

    def to_dict(self) -> Dict[str, Any]:
        return {"rooms": [r.to_dict() if hasattr(r, "to_dict") else r for r in self.rooms]}


@dataclass
class UserProfilePayload:
    username: str
    rating: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthStatusPayload:
    status: str
    service: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameAllocatePayload:
    room_id: str
    player1: str
    player2: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameAssignedPayload:
    room_id: str
    game_server_id: str
    player1: str
    player2: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameCommandPayload:
    room_id: str
    username: str
    gateway_id: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameStatePayload:
    room_id: str
    state: Dict[str, Any]
    target_username: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameFinishedPayload:
    room_id: str
    winner: Optional[str] = None
    reason: Optional[str] = None
    final_ratings: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlayerConnectedPayload:
    gateway_id: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlayerDisconnectedPayload:
    gateway_id: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def encode_json(data: Dict[str, Any]) -> bytes:
    """Serializes dictionary to UTF-8 JSON bytes for NATS payloads."""
    return json.dumps(data).encode("utf-8")


def decode_json(payload: bytes) -> Dict[str, Any]:
    """Deserializes UTF-8 JSON bytes from NATS payloads to dictionary."""
    return json.loads(payload.decode("utf-8"))
