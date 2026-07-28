from dataclasses import dataclass, field, asdict, is_dataclass
from enum import Enum
import json
from typing import Optional, List, Dict, Any, Type
from shared.protocol.message_type import MessageType
from shared.models.color import Color
from shared.models.cell import Cell



@dataclass
class BaseMessage:
    """Base class for network protocol messages."""
    type: Optional[MessageType] = field(default=None)




@dataclass
class AuthMessage(BaseMessage):
    username: str = ""
    password: str = ""
    token: Optional[str] = None
    type: MessageType = MessageType.AUTH


@dataclass
class AuthResponseMessage(BaseMessage):
    success: bool = False
    username: Optional[str] = None
    rating: Optional[int] = None
    error: Optional[str] = None
    type: MessageType = MessageType.AUTH_RESPONSE


@dataclass
class HeartbeatMessage(BaseMessage):
    type: MessageType = MessageType.HEARTBEAT


@dataclass
class HeartbeatAckMessage(BaseMessage):
    type: MessageType = MessageType.HEARTBEAT_ACK


@dataclass
class ErrorMessage(BaseMessage):
    message: str = ""
    type: MessageType = MessageType.ERROR


@dataclass
class MatchmakingMessage(BaseMessage):
    type: MessageType = MessageType.MATCHMAKING


@dataclass
class LeaveMatchmakingMessage(BaseMessage):
    type: MessageType = MessageType.LEAVE_MATCHMAKING


@dataclass
class MatchmakingStatusMessage(BaseMessage):
    status: str = ""
    type: MessageType = MessageType.MATCHMAKING_STATUS


@dataclass
class CreateRoomMessage(BaseMessage):
    room_id: Optional[str] = None
    type: MessageType = MessageType.CREATE_ROOM


@dataclass
class JoinRoomMessage(BaseMessage):
    room_id: str = ""
    type: MessageType = MessageType.JOIN_ROOM


@dataclass
class LeaveRoomMessage(BaseMessage):
    type: MessageType = MessageType.LEAVE_ROOM


@dataclass
class RoomStateMessage(BaseMessage):
    room_id: Optional[str] = None
    status: Optional[str] = None
    white: Optional[str] = None
    black: Optional[str] = None
    spectators: List[str] = field(default_factory=list)
    your_color: Color = None
    type: MessageType = MessageType.ROOM_STATE




@dataclass
class MoveMessage(BaseMessage):
    from_cell: Cell = None
    to_cell: Cell = None
    type: MessageType = MessageType.MOVE


@dataclass
class JumpMessage(BaseMessage):
    cell: Cell = None
    type: MessageType = MessageType.JUMP


@dataclass
class GetSnapshotMessage(BaseMessage):
    type: MessageType = MessageType.GET_SNAPSHOT


@dataclass
class SnapshotMessage(BaseMessage):
    data: Dict[str, Any] = field(default_factory=dict)
    type: MessageType = MessageType.SNAPSHOT


@dataclass
class CountdownMessage(BaseMessage):
    seconds: int = 0
    message: Optional[str] = None
    type: MessageType = MessageType.COUNTDOWN


@dataclass
class GameOverMessage(BaseMessage):
    winner: Optional[str] = None
    reason: Optional[str] = None
    white_rating: Optional[int] = None
    black_rating: Optional[int] = None
    message: Optional[str] = None
    type: MessageType = MessageType.GAME_OVER


MESSAGE_CLASSES: Dict[Any, Type[BaseMessage]] = {
    MessageType.AUTH: AuthMessage,
    MessageType.AUTH.value: AuthMessage,
    MessageType.AUTH_RESPONSE: AuthResponseMessage,
    MessageType.AUTH_RESPONSE.value: AuthResponseMessage,
    MessageType.HEARTBEAT: HeartbeatMessage,
    MessageType.HEARTBEAT.value: HeartbeatMessage,
    MessageType.HEARTBEAT_ACK: HeartbeatAckMessage,
    MessageType.HEARTBEAT_ACK.value: HeartbeatAckMessage,
    MessageType.ERROR: ErrorMessage,
    MessageType.ERROR.value: ErrorMessage,
    MessageType.MATCHMAKING: MatchmakingMessage,
    MessageType.MATCHMAKING.value: MatchmakingMessage,
    MessageType.LEAVE_MATCHMAKING: LeaveMatchmakingMessage,
    MessageType.LEAVE_MATCHMAKING.value: LeaveMatchmakingMessage,
    MessageType.MATCHMAKING_STATUS: MatchmakingStatusMessage,
    MessageType.MATCHMAKING_STATUS.value: MatchmakingStatusMessage,
    MessageType.CREATE_ROOM: CreateRoomMessage,
    MessageType.CREATE_ROOM.value: CreateRoomMessage,
    MessageType.JOIN_ROOM: JoinRoomMessage,
    MessageType.JOIN_ROOM.value: JoinRoomMessage,
    MessageType.LEAVE_ROOM: LeaveRoomMessage,
    MessageType.LEAVE_ROOM.value: LeaveRoomMessage,
    MessageType.ROOM_STATE: RoomStateMessage,
    MessageType.ROOM_STATE.value: RoomStateMessage,
    MessageType.MOVE: MoveMessage,
    MessageType.MOVE.value: MoveMessage,
    MessageType.JUMP: JumpMessage,
    MessageType.JUMP.value: JumpMessage,
    MessageType.GET_SNAPSHOT: GetSnapshotMessage,
    MessageType.GET_SNAPSHOT.value: GetSnapshotMessage,
    MessageType.SNAPSHOT: SnapshotMessage,
    MessageType.SNAPSHOT.value: SnapshotMessage,
    MessageType.COUNTDOWN: CountdownMessage,
    MessageType.COUNTDOWN.value: CountdownMessage,
    MessageType.GAME_OVER: GameOverMessage,
    MessageType.GAME_OVER.value: GameOverMessage,
}


def serialize_message(msg: Any) -> str:
    """Serializes a network protocol message object or dict into a JSON string."""
    if is_dataclass(msg) and not isinstance(msg, type):
        data = asdict(msg)
    elif isinstance(msg, dict):
        data = msg
    else:
        raise ValueError(f"Cannot serialize object of type {type(msg)}")

    def json_default(obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(data, default=json_default)


def _parse_message_kwargs(msg_cls: Type[BaseMessage], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to convert dictionary parameters into typed Cell instances."""
    if "from_cell" in kwargs and isinstance(kwargs["from_cell"], dict):
        kwargs["from_cell"] = Cell(**kwargs["from_cell"])
    if "to_cell" in kwargs and isinstance(kwargs["to_cell"], dict):
        kwargs["to_cell"] = Cell(**kwargs["to_cell"])
    if "cell" in kwargs and isinstance(kwargs["cell"], dict) and msg_cls == JumpMessage:
        kwargs["cell"] = Cell(**kwargs["cell"])
    return kwargs



def deserialize_message(raw: str) -> BaseMessage:
    """Deserializes a JSON string into its corresponding BaseMessage dataclass instance."""
    try:
        data = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object dictionary, got {type(data).__name__}")

    raw_type = data.get("type")
    if isinstance(raw_type, MessageType):
        msg_type = raw_type
    elif isinstance(raw_type, str):
        try:
            msg_type = MessageType(raw_type)
        except ValueError:
            raise ValueError(f"Unknown message type: {raw_type}")
    else:
        raise ValueError(f"Missing or invalid message type: {raw_type}")

    msg_cls = MESSAGE_CLASSES.get(msg_type)
    if not msg_cls:
        raise ValueError(f"Unknown message type: {raw_type}")

    kwargs = dict(data)
    kwargs["type"] = msg_type
    kwargs = _parse_message_kwargs(msg_cls, kwargs)

    return msg_cls(**kwargs)





