from shared.models.game_snapshot import GameSnapshot
from shared.models.piece_type import PieceType

class UIHistoryTracker:
    def __init__(self):
        self.history = []
        self.tracked_moves = {}
        self.prev_grid = None

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

        disappeared_keys = [k for k in self.tracked_moves if k not in current_keys]
        for key in disappeared_keys:
            move = self.tracked_moves[key]
            
            grid = snapshot.board.grid
            to_y, to_x = move.to_pos.y, move.to_pos.x
            success = False
            
            if 0 <= to_y < len(grid) and 0 <= to_x < len(grid[0]):
                target_piece = grid[to_y][to_x]
                if target_piece is not None and target_piece.color == move.piece.color:
                    if target_piece.kind == move.piece.kind:
                        success = True
                    elif move.piece.kind == PieceType.PAWN and target_piece.kind == PieceType.QUEEN:
                        success = True
            
            if success:
                is_capture = False
                if self.prev_grid is not None and 0 <= to_y < len(self.prev_grid) and 0 <= to_x < len(self.prev_grid[0]):
                    prev_piece = self.prev_grid[to_y][to_x]
                    if prev_piece is not None and prev_piece.color != move.piece.color:
                        is_capture = True
                
                self.history.append({
                    "time": move.arrival,
                    "color": move.piece.color,
                    "kind": move.piece.kind,
                    "from_pos": move.from_pos,
                    "to_pos": move.to_pos,
                    "is_capture": is_capture
                })
            
            del self.tracked_moves[key]

        self.prev_grid = snapshot.board.grid
