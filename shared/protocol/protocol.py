from typing import Any, Optional, Tuple
from shared.models.cell import Cell
from shared.models.game_snapshot import GameSnapshot, BoardSnapshot, PieceSnapshot, PendingMoveSnapshot, JumpSnapshot


def cell_to_dict(cell: Optional[Cell]) -> Optional[dict]:
    """Serializes a Cell object to a dictionary."""
    if cell is None:
        return None
    return {"y": cell.y, "x": cell.x}

def dict_to_cell(d: Optional[dict]) -> Optional[Cell]:
    """Deserializes a dictionary to a Cell object."""
    if d is None:
        return None
    return Cell(y=d["y"], x=d["x"])

def piece_to_dict(piece: Optional[PieceSnapshot]) -> Optional[dict]:
    """Serializes a PieceSnapshot to a dictionary."""
    if piece is None:
        return None
    return {
        "color": piece.color,
        "kind": piece.kind,
        "cell": cell_to_dict(piece.cell),
        "cooldown_until": piece.cooldown_until,
        "status": piece.status
    }

def dict_to_piece(d: Optional[dict]) -> Optional[PieceSnapshot]:
    """Deserializes a dictionary to a PieceSnapshot."""
    if d is None:
        return None
    return PieceSnapshot(
        color=d["color"],
        kind=d["kind"],
        cell=dict_to_cell(d["cell"]),
        cooldown_until=d["cooldown_until"],
        status=d["status"]
    )

def board_to_dict(board: BoardSnapshot) -> dict:
    """Serializes a BoardSnapshot to a dictionary."""
    grid_list = []
    for row in board.grid:
        row_list = []
        for piece in row:
            row_list.append(piece_to_dict(piece))
        grid_list.append(row_list)
        
    return {
        "grid": grid_list,
        "width": board.width,
        "height": board.height
    }

def dict_to_board(d: dict) -> BoardSnapshot:
    """Deserializes a dictionary to a BoardSnapshot."""
    grid_list = []
    for row in d["grid"]:
        row_list = []
        for piece_dict in row:
            row_list.append(dict_to_piece(piece_dict))
        grid_list.append(tuple(row_list))
        
    return BoardSnapshot(
        grid=tuple(grid_list),
        width=d["width"],
        height=d["height"]
    )

def move_to_dict(move: PendingMoveSnapshot) -> dict:
    """Serializes a PendingMoveSnapshot to a dictionary."""
    return {
        "from_pos": cell_to_dict(move.from_pos),
        "to_pos": cell_to_dict(move.to_pos),
        "piece": piece_to_dict(move.piece),
        "arrival": move.arrival,
        "is_captured": move.is_captured,
        "path": [cell_to_dict(c) for c in move.path]
    }

def dict_to_move(d: dict) -> PendingMoveSnapshot:
    """Deserializes a dictionary to a PendingMoveSnapshot."""
    return PendingMoveSnapshot(
        from_pos=dict_to_cell(d["from_pos"]),
        to_pos=dict_to_cell(d["to_pos"]),
        piece=dict_to_piece(d["piece"]),
        arrival=d["arrival"],
        is_captured=d["is_captured"],
        path=tuple(dict_to_cell(c) for c in d["path"])
    )

def jump_to_dict(jump: JumpSnapshot) -> dict:
    """Serializes a JumpSnapshot to a dictionary."""
    return {
        "cell": list(jump.cell),
        "start": jump.start,
        "end": jump.end,
        "piece": piece_to_dict(jump.piece)
    }

def dict_to_jump(d: dict) -> JumpSnapshot:
    """Deserializes a dictionary to a JumpSnapshot."""
    return JumpSnapshot(
        cell=tuple(d["cell"]),
        start=d["start"],
        end=d["end"],
        piece=dict_to_piece(d["piece"])
    )

def serialize_snapshot(snapshot: GameSnapshot) -> dict:
    """Converts a GameSnapshot dataclass into a JSON-serializable dictionary."""
    return {
        "board": board_to_dict(snapshot.board),
        "selected_piece": piece_to_dict(snapshot.selected_piece),
        "game_over": snapshot.game_over,
        "clock": snapshot.clock,
        "pending_moves": [move_to_dict(m) for m in snapshot.pending_moves],
        "jumps": [jump_to_dict(j) for j in snapshot.jumps]
    }

def deserialize_snapshot(d: dict) -> GameSnapshot:
    """Converts a JSON-deserialized dictionary back into a GameSnapshot dataclass."""
    return GameSnapshot(
        board=dict_to_board(d["board"]),
        selected_piece=dict_to_piece(d["selected_piece"]),
        game_over=d["game_over"],
        clock=d["clock"],
        pending_moves=tuple(dict_to_move(m) for m in d["pending_moves"]),
        jumps=tuple(dict_to_jump(j) for j in d["jumps"])
    )

