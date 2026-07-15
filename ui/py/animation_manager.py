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
        remaining_snaps = self._gather_active_piece_snapshots(snapshot)
        next_views = self._match_and_update_existing_views(remaining_snaps)
        new_views = self._create_new_piece_views(remaining_snaps, snapshot)
        self.active_views = next_views + new_views

    def _gather_active_piece_snapshots(self, snapshot: GameSnapshot) -> list:
        """Gathers all active piece snapshots from the board grid."""
        remaining_snaps = []
        board = snapshot.board
        for row in board.grid:
            for p in row:
                if p is not None:
                    remaining_snaps.append(p)
        return remaining_snaps

    def _match_and_update_existing_views(self, remaining_snaps: list) -> list[PieceView]:
        """
        Matches existing piece views with snapshots to preserve their animation state,
        updating cell coordinates and returning the matched views.
        Mutates `remaining_snaps` by removing matched snapshots.
        """
        next_views = []
        for view in self.active_views:
            matched_snap = self._find_matching_snapshot(view, remaining_snaps)
            if matched_snap is not None:
                view.cell = matched_snap.cell
                next_views.append(view)
                remaining_snaps.remove(matched_snap)
        return next_views

    def _find_matching_snapshot(self, view: PieceView, remaining_snaps: list):
        """Finds a matching snapshot for a given PieceView from the remaining list."""
        # Look for exact match (same color, kind, and cell)
        for snap in remaining_snaps:
            if snap.color == view.color and snap.kind == view.kind and snap.cell == view.cell:
                return snap

        # If not found by cell, check if the piece is in transit/arrived using cached target_cell
        if hasattr(view, "target_cell"):
            for snap in remaining_snaps:
                if snap.color == view.color and snap.kind == view.kind and snap.cell == view.target_cell:
                    return snap

        return None

    def _create_new_piece_views(self, remaining_snaps: list, snapshot: GameSnapshot) -> list[PieceView]:
        """Creates new PieceView instances for any remaining (newly spawned) snapshots."""
        new_views = []
        for snap in remaining_snaps:
            new_view = PieceView(
                color=snap.color,
                kind=snap.kind,
                cell=snap.cell,
                geometry=self.geometry,
                asset_loader=self.asset_loader,
                snapshot=snapshot
            )
            new_views.append(new_view)
        return new_views

    def update(self, dt: float, snapshot: GameSnapshot) -> None:
        """Ticks active animations for all visible pieces."""
        for view in self.active_views:
            view.update(dt, snapshot)
