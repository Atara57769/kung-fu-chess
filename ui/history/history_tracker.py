from models.game_snapshot import GameSnapshot
from models.piece_type import PieceType

class UIHistoryTracker:
    def __init__(self):
        # List of dicts: {"time": int, "color": str, "kind": str, "to_pos": Cell}
        self.history = []
        # Key: (from_y, from_x, to_y, to_x, color, kind, arrival) -> move_snapshot
        self.tracked_moves = {}

    def update(self, snapshot: GameSnapshot) -> None:
        current_keys = set()
        for move in snapshot.pending_moves:
            key = (
                move.from_pos.y, move.from_pos.x,
                move.to_pos.y, move.to_pos.x,
                move.piece.color, move.piece.kind,
                move.arrival
            )
            current_keys.add(key)
            if key not in self.tracked_moves:
                self.tracked_moves[key] = move

        # Check for moves that disappeared
        disappeared_keys = [k for k in self.tracked_moves if k not in current_keys]
        for key in disappeared_keys:
            move = self.tracked_moves[key]
            
            # Check if this move successfully completed on the board
            grid = snapshot.board.grid
            to_y, to_x = move.to_pos.y, move.to_pos.x
            success = False
            
            if 0 <= to_y < len(grid) and 0 <= to_x < len(grid[0]):
                target_piece = grid[to_y][to_x]
                if target_piece is not None and target_piece.color == move.piece.color:
                    if target_piece.kind == move.piece.kind:
                        success = True
                    elif move.piece.kind == PieceType.PAWN and target_piece.kind == PieceType.QUEEN:
                        # Pawn promotion to Queen
                        success = True
            
            if success:
                self.history.append({
                    "time": move.arrival,
                    "color": move.piece.color,
                    "kind": move.piece.kind,
                    "to_pos": move.to_pos
                })
            
            del self.tracked_moves[key]
