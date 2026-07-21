from enum import Enum

class MessageType(str, Enum):
    """Enumeration of all network protocol message and event types."""
    AUTH = "auth"
    AUTH_RESPONSE = "auth_response"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    ERROR = "error"

    MATCHMAKING = "matchmaking"
    LEAVE_MATCHMAKING = "leave_matchmaking"
    MATCHMAKING_STATUS = "matchmaking_status"
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_STATE = "room_state"

    CLICK = "click"
    JUMP = "jump"
    GET_SNAPSHOT = "get_snapshot"
    SNAPSHOT = "snapshot"
    COUNTDOWN = "countdown"
    GAME_OVER = "game_over"
