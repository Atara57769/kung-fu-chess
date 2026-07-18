import pytest
from models.cell import Cell
from models.pieces import Piece, PieceStatus
from models.board import Board
from models.pending_move import PendingMove
from models.jump import Jump
from models.game_state import GameState
from models.game_snapshot import (
    PieceSnapshot,
    BoardSnapshot,
    PendingMoveSnapshot,
    JumpSnapshot,
    GameSnapshot,
)

def test_piece_snapshot_none():
    assert PieceSnapshot.from_piece(None) is None

def test_piece_snapshot_valid():
    p = Piece.from_text("wP")
    p.cell = Cell(1, 2)
    p.cooldown_until = 500
    p.status = PieceStatus.MOVING
    
    snap = PieceSnapshot.from_piece(p)
    assert snap.color == "w"
    assert snap.kind == "P"
    assert snap.cell == Cell(1, 2)
    assert snap.cooldown_until == 500
    assert snap.status == "MOVING"

def test_board_snapshot():
    board = Board(grid=[[None, None], [None, None]], width=2, height=2)
    p = Piece.from_text("bK")
    board.grid[0][0] = p
    p.cell = Cell(0, 0)
    
    snap = BoardSnapshot.from_board(board)
    assert snap.width == 2
    assert snap.height == 2
    assert snap.grid[0][0].color == "b"
    assert snap.grid[0][0].kind == "K"
    assert snap.grid[0][1] is None

def test_pending_move_snapshot():
    p = Piece.from_text("wN")
    move = PendingMove(
        from_pos=Cell(0, 0),
        to_pos=Cell(1, 2),
        piece=p,
        arrival=1000
    )
    move.is_captured = True
    
    snap = PendingMoveSnapshot.from_pending_move(move)
    assert snap.from_pos == Cell(0, 0)
    assert snap.to_pos == Cell(1, 2)
    assert snap.piece.color == "w"
    assert snap.piece.kind == "N"
    assert snap.arrival == 1000
    assert snap.is_captured is True
    assert snap.path == (Cell(0, 0), Cell(1, 2))

def test_jump_snapshot():
    p = Piece.from_text("wP")
    jump = Jump(cell=(1, 1), start=200, end=400, piece=p)
    snap = JumpSnapshot.from_jump(jump)
    assert snap.cell == (1, 1)
    assert snap.start == 200
    assert snap.end == 400
    assert snap.piece.color == "w"

def test_game_snapshot():
    board = Board(grid=[[None, None, None], [None, None, None], [None, None, None]], width=3, height=3)
    state = GameState(board=board)
    state.game_over = True
    state.clock = 42
    
    p = Piece.from_text("wP")
    state.selected_piece = p
    
    move = PendingMove(Cell(0, 0), Cell(1, 1), p, 100)
    state.pending_moves.append(move)
    
    jump = Jump((2, 2), 10, 20, p)
    state.jumps.append(jump)
    
    snap = GameSnapshot.from_state(state)
    assert snap.game_over is True
    assert snap.clock == 42
    assert snap.selected_piece.color == "w"
    assert len(snap.pending_moves) == 1
    assert len(snap.jumps) == 1

