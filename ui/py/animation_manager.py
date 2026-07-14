from models.game_snapshot import GameSnapshot
from ui.py.board_geometry import BoardGeometry
from ui.py.piece_view import PieceView

class AnimationManager:
    def __init__(self, geometry: BoardGeometry, asset_loader):
        self.geometry = geometry
        self.asset_loader = asset_loader
        self.active_views: list[PieceView] = []

    def sync_pieces(self, snapshot: GameSnapshot) -> None:
        """
        Synchronizes the list of visual PieceViews with the pieces on the board in the snapshot.
        Preserves existing views to maintain ongoing animation states (idle, move, rest).
        """
        # 1. Gather all active piece snapshots from the board grid
        remaining_snaps = []
        board = snapshot.board
        for row in board.grid:
            for p in row:
                if p is not None:
                    remaining_snaps.append(p)

        next_views = []

        # 2. Match existing piece views with snapshots to preserve their animation state
        for view in self.active_views:
            matched_snap = None

            # Look for exact match (same color, kind, and cell)
            for snap in remaining_snaps:
                if snap.color == view.color and snap.kind == view.kind and snap.cell == view.cell:
                    matched_snap = snap
                    break

            # If not found by cell, check if the piece is in transit/arrived using cached target_cell
            if matched_snap is None and hasattr(view, "target_cell"):
                for snap in remaining_snaps:
                    if snap.color == view.color and snap.kind == view.kind and snap.cell == view.target_cell:
                        matched_snap = snap
                        break

            if matched_snap is not None:
                # Update cell coordinates (handles move completion)
                view.cell = matched_snap.cell
                next_views.append(view)
                remaining_snaps.remove(matched_snap)

        # 3. Create new views for any remaining (newly spawned) snapshots
        for snap in remaining_snaps:
            new_view = PieceView(
                color=snap.color,
                kind=snap.kind,
                cell=snap.cell,
                geometry=self.geometry,
                asset_loader=self.asset_loader,
                snapshot=snapshot
            )
            next_views.append(new_view)

        self.active_views = next_views

    def update(self, dt: float, snapshot: GameSnapshot) -> None:
        """Ticks active animations for all visible pieces."""
        for view in self.active_views:
            view.update(dt, snapshot)
