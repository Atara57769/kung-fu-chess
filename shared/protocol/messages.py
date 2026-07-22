from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional, List, Dict, Any, Type
from shared.protocol.message_type import MessageType


@dataclass
class BaseMessage:
    """Base class for network protocol messages."""
    type: str = ""



@dataclass
class AuthMessage(BaseMessage):
    username: str = ""
    password: str = ""
    type: str = MessageType.AUTH.value


@dataclass
class AuthResponseMessage(BaseMessage):
    success: bool = False
    username: Optional[str] = None
    rating: Optional[int] = None
    error: Optional[str] = None
    type: str = MessageType.AUTH_RESPONSE.value


@dataclass
class HeartbeatMessage(BaseMessage):
    type: str = MessageType.HEARTBEAT.value


@dataclass
class HeartbeatAckMessage(BaseMessage):
    type: str = MessageType.HEARTBEAT_ACK.value


@dataclass
class ErrorMessage(BaseMessage):
    message: str = ""
    type: str = MessageType.ERROR.value


@dataclass
class MatchmakingMessage(BaseMessage):
    type: str = MessageType.MATCHMAKING.value


@dataclass
class LeaveMatchmakingMessage(BaseMessage):
    type: str = MessageType.LEAVE_MATCHMAKING.value


@dataclass
class MatchmakingStatusMessage(BaseMessage):
    status: str = ""
    type: str = MessageType.MATCHMAKING_STATUS.value


@dataclass
class CreateRoomMessage(BaseMessage):
    room_id: Optional[str] = None
    type: str = MessageType.CREATE_ROOM.value


@dataclass
class JoinRoomMessage(BaseMessage):
    room_id: str = ""
    type: str = MessageType.JOIN_ROOM.value


@dataclass
class LeaveRoomMessage(BaseMessage):
    type: str = MessageType.LEAVE_ROOM.value


@dataclass
class RoomStateMessage(BaseMessage):
    room_id: Optional[str] = None
    status: Optional[str] = None
    white: Optional[str] = None
    black: Optional[str] = None
    spectators: List[str] = field(default_factory=list)
    your_color: Optional[str] = None
    type: str = MessageType.ROOM_STATE.value


@dataclass
class MoveMessage(BaseMessage):
    data: str = ""
    type: str = MessageType.MOVE.value


@dataclass
class JumpMessage(BaseMessage):
    data: str = ""
    type: str = MessageType.JUMP.value


@dataclass
class GetSnapshotMessage(BaseMessage):
    type: str = MessageType.GET_SNAPSHOT.value


@dataclass
class SnapshotMessage(BaseMessage):
    data: Dict[str, Any] = field(default_factory=dict)
    type: str = MessageType.SNAPSHOT.value


@dataclass
class CountdownMessage(BaseMessage):
    seconds: int = 0
    message: Optional[str] = None
    type: str = MessageType.COUNTDOWN.value


@dataclass
class GameOverMessage(BaseMessage):
    winner: Optional[str] = None
    reason: Optional[str] = None
    white_rating_change: Optional[str] = None
    black_rating_change: Optional[str] = None
    message: Optional[str] = None
    type: str = MessageType.GAME_OVER.value


MESSAGE_CLASSES: Dict[str, Type[BaseMessage]] = {
    MessageType.AUTH.value: AuthMessage,
    MessageType.AUTH_RESPONSE.value: AuthResponseMessage,
    MessageType.HEARTBEAT.value: HeartbeatMessage,
    MessageType.HEARTBEAT_ACK.value: HeartbeatAckMessage,
    MessageType.ERROR.value: ErrorMessage,
    MessageType.MATCHMAKING.value: MatchmakingMessage,
    MessageType.LEAVE_MATCHMAKING.value: LeaveMatchmakingMessage,
    MessageType.MATCHMAKING_STATUS.value: MatchmakingStatusMessage,
    MessageType.CREATE_ROOM.value: CreateRoomMessage,
    MessageType.JOIN_ROOM.value: JoinRoomMessage,
    MessageType.LEAVE_ROOM.value: LeaveRoomMessage,
    MessageType.ROOM_STATE.value: RoomStateMessage,
    MessageType.MOVE.value: MoveMessage,
    MessageType.JUMP.value: JumpMessage,
    MessageType.GET_SNAPSHOT.value: GetSnapshotMessage,
    MessageType.SNAPSHOT.value: SnapshotMessage,
    MessageType.COUNTDOWN.value: CountdownMessage,
    MessageType.GAME_OVER.value: GameOverMessage,
}


def parse_message(data: Dict[str, Any]) -> BaseMessage:
    """Parses a dictionary into its corresponding message dataclass instance."""
    msg_type = data.get("type")
    if isinstance(msg_type, MessageType):
        msg_type = msg_type.value
    msg_cls = MESSAGE_CLASSES.get(msg_type)
    if not msg_cls:
        raise ValueError(f"Unknown message type: {msg_type}")
    return msg_cls(**data)
