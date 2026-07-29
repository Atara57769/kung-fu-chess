"""
NATS Subjects Constants for Distributed Kung-Fu Chess Services.
"""

# Auth subjects
AUTH_LOGIN = "auth.login"
AUTH_RESULT = "auth.result"
AUTH_REGISTER = "auth.register"

# Matchmaking subjects
MATCHMAKING_REQUEST = "matchmaking.request"
MATCHMAKING_MATCH_FOUND = "matchmaking.match_found"
MATCHMAKING_TIMEOUT = "matchmaking.timeout"

# Room subjects
ROOM_CREATE = "room.create"
ROOM_CREATED = "room.created"
ROOM_JOIN = "room.join"
ROOM_JOINED = "room.joined"
ROOM_LEAVE = "room.leave"
ROOM_UPDATED = "room.updated"

# Game Allocation & Shard subjects
GAME_ALLOCATE = "game.allocate"
GAME_ASSIGNED = "game.assigned"
GAME_COMMAND = "game.command"
GAME_STATE = "game.state"
GAME_FINISHED = "game.finished"
GAME_EVENTS = "game.events"

# Player presence subjects
PLAYER_CONNECTED = "player.connected"
PLAYER_DISCONNECTED = "player.disconnected"
