import pytest
from models.color import Color
from models.piece_type import PieceType
from models.game_state import GameState
from models.cell import Cell
from models.pieces import Piece
from services.board_parser import TextBoardParser
from core.events import EventBus, GameStarted, PieceCaptured, PieceMoved, GameEnded, ScoreChanged
from services.score_tracker import ScoreTracker
from engine.game_engine import GameEngine
from engine.controller import Controller

def test_event_bus_integration_flow():
    # 1. Setup Event Bus and Score Tracker
    bus = EventBus()
    tracker = ScoreTracker(bus)

    # Listen to ScoreChanged to verify score events
    score_events = []
    bus.subscribe(ScoreChanged, lambda e: score_events.append((e.white_score, e.black_score)))

    # Listen to other events for verification
    captured_events = []
    moved_events = []
    ended_events = []
    bus.subscribe(PieceCaptured, lambda e: captured_events.append(e))
    bus.subscribe(PieceMoved, lambda e: moved_events.append(e))
    bus.subscribe(GameEnded, lambda e: ended_events.append(e))

    # 2. Setup board with wK, wP, bK, bR
    # White initial points: King (0) + Pawn (1) = 1
    # Black initial points: King (0) + Rook (5) = 5
    board = TextBoardParser().parse([
        "wK . . bK",
        "wP . . bR"
    ])
    state = GameState(board=board)
    engine = GameEngine(event_bus=bus)
    
    # 3. Initialize Controller (should fire GameStarted)
    controller = Controller(state, game_engine=engine, stdout=None, event_bus=bus)

    # Verify GameStarted calculated initial scores correctly
    assert tracker.white_score == 1
    assert tracker.black_score == 5
    # Verification that ScoreChanged was published on initialization
    assert (1, 5) in score_events

    # Clear score events for next action
    score_events.clear()

    # 4. Perform a move where White Pawn captures Black Rook
    # We will simulate a pending move completing to bypass rule verification for raw execution
    # Move is: wP (1, 0) to bR (1, 3)
    pawn = board.get_piece_at(Cell(1, 0))
    arrival_time = 1000
    move = engine.move_scheduler.create_pending_move(
        from_cell=Cell(1, 0),
        to_cell=Cell(1, 3),
        piece=pawn,
        arrival=arrival_time
    )
    engine.move_scheduler.add_to_pending(state, move)

    # Tick clock forward to trigger movement resolution in arbiter
    engine.wait(state, 1000)

    # Verify that the move resolved and piece was moved on board
    assert board.get_piece_at(Cell(1, 0)) is None
    assert board.get_piece_at(Cell(1, 3)) == pawn

    # Verify PieceCaptured event was published with proper enums
    assert len(captured_events) == 1
    cap = captured_events[0]
    assert cap.attacker_color == Color.WHITE
    assert cap.victim_color == Color.BLACK
    assert cap.victim_kind == PieceType.ROOK

    assert len(moved_events) == 1
    assert moved_events[0].from_pos == Cell(1, 0)
    assert moved_events[0].to_pos == Cell(1, 3)

    # Verify ScoreTracker updated scores and published ScoreChanged
    assert tracker.white_score == 1
    assert tracker.black_score == 0  # Black lost Rook (5 points)
    assert score_events[-1] == (1, 0)

    # 5. Capture the King to end the game
    score_events.clear()
    captured_events.clear()

    # Move is: wP (1, 3) to bK (0, 3)
    king_move = engine.move_scheduler.create_pending_move(
        from_cell=Cell(1, 3),
        to_cell=Cell(0, 3),
        piece=pawn,
        arrival=state.clock + 1000
    )
    engine.move_scheduler.add_to_pending(state, king_move)
    engine.wait(state, 1000)

    # Verify PieceCaptured for King
    assert len(captured_events) == 1
    cap_king = captured_events[0]
    assert cap_king.attacker_color == Color.WHITE
    assert cap_king.victim_color == Color.BLACK
    assert cap_king.victim_kind == PieceType.KING

    # Verify GameEnded was published with Color.WHITE winning
    assert len(ended_events) == 1
    assert ended_events[0].winner == Color.WHITE
    assert state.game_over is True
