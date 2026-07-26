import asyncio
import time
from typing import List, Optional
from shared.constants import DEFAULT_BOARD_LAYOUT, ROOM_STATUS_WAITING
from server.game.engine.game_engine import GameEngine
from shared.models.game_state import GameState
from shared.models.color import Color
from server.game.services.board_parser import TextBoardParser

class ConnectedPlayer:
    """Represents a connection session for a player."""
    def __init__(self, ws, ip_address: str) -> None:
        self.ws = ws
        self.ip_address = ip_address
        self.username: Optional[str] = None
        self.rating: int = 1200
        self.authenticated: bool = False
        self.room_id: Optional[str] = None
        self.color: Optional[Color] = None  
        self.last_heartbeat: float = time.time()

class GameRoom:
    """Represents a game lobby or match session."""
    def __init__(self, room_id: str) -> None:
        self.room_id = room_id
        self.white_player: Optional[ConnectedPlayer] = None
        self.black_player: Optional[ConnectedPlayer] = None
        self.spectators: List[ConnectedPlayer] = []
        
        self.board = TextBoardParser().parse(DEFAULT_BOARD_LAYOUT)
        self.state = GameState(board=self.board)
        
        from server.game.engine.game_engine import GameEngine
        from server.game.engine.controller import Controller
        self.controller = Controller(self.state, GameEngine())
        
        self.status: str = ROOM_STATUS_WAITING
        self.countdown_task: Optional[asyncio.Task] = None
        self.countdown_seconds: int = 0
        self.tick_task: Optional[asyncio.Task] = None
