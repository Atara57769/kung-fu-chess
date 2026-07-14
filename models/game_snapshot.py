from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING
from models.cell import Cell

if TYPE_CHECKING:
    from models.pieces import Piece
    from models.board import Board
    from models.pending_move import PendingMove
    from models.jump import Jump
    from models.game_state import GameState


@dataclass(frozen=True)
class PieceSnapshot:
    color: str
    kind: str
    cell: Optional[Cell] = None
    cooldown_until: int = 0

    @classmethod
    def from_piece(cls, piece: Optional['Piece']) -> Optional['PieceSnapshot']:
        if piece is None:
            return None
        return cls(
            color=piece.color,
            kind=piece.kind,
            cell=piece.cell,
            cooldown_until=piece.cooldown_until,
        )


@dataclass(frozen=True)
class BoardSnapshot:
    grid: Tuple[Tuple[Optional[PieceSnapshot], ...], ...]
    width: int
    height: int

    @classmethod
    def from_board(cls, board: 'Board') -> 'BoardSnapshot':
        grid_snapshot = tuple(
            tuple(PieceSnapshot.from_piece(p) for p in row)
            for row in board.grid
        )
        return cls(
            grid=grid_snapshot,
            width=board.width,
            height=board.height,
        )


@dataclass(frozen=True)
class PendingMoveSnapshot:
    from_pos: Cell
    to_pos: Cell
    piece: PieceSnapshot
    arrival: int
    is_captured: bool
    path: Tuple[Cell, ...]

    @classmethod
    def from_pending_move(cls, move: 'PendingMove') -> 'PendingMoveSnapshot':
        return cls(
            from_pos=move.from_pos,
            to_pos=move.to_pos,
            piece=PieceSnapshot.from_piece(move.piece),
            arrival=move.arrival,
            is_captured=move.is_captured,
            path=tuple(move.path),
        )


@dataclass(frozen=True)
class JumpSnapshot:
    cell: Tuple[int, int]
    start: int
    end: int
    piece: PieceSnapshot

    @classmethod
    def from_jump(cls, jump: 'Jump') -> 'JumpSnapshot':
        return cls(
            cell=jump.cell,
            start=jump.start,
            end=jump.end,
            piece=PieceSnapshot.from_piece(jump.piece),
        )


@dataclass(frozen=True)
class GameSnapshot:
    board: BoardSnapshot
    selected_piece: Optional[PieceSnapshot]
    game_over: bool
    clock: int
    pending_moves: Tuple[PendingMoveSnapshot, ...]
    jumps: Tuple[JumpSnapshot, ...]

    @classmethod
    def from_state(cls, state: 'GameState') -> 'GameSnapshot':
        return cls(
            board=BoardSnapshot.from_board(state.board),
            selected_piece=PieceSnapshot.from_piece(state.selected_piece),
            game_over=state.game_over,
            clock=state.clock,
            pending_moves=tuple(PendingMoveSnapshot.from_pending_move(m) for m in state.pending_moves),
            jumps=tuple(JumpSnapshot.from_jump(j) for j in state.jumps),
        )
