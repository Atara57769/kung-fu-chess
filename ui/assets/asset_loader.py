import os
import json
import pathlib
from ui.rendering.img import Img
from constants import CELL_SIZE

class PieceAsset:
    def __init__(self, color: str, kind: str, state_name: str, config: dict, sprites: list[Img]):
        self.color: str = color.lower()
        self.kind: str = kind.upper()
        self.state_name: str = state_name
        self.config: dict = config
        self.sprites: list[Img] = sprites


class AssetLoader:
    def __init__(self, base_dir: str | pathlib.Path = None, 
                 piece_size: tuple[int, int] = (CELL_SIZE, CELL_SIZE),
                 board_size: tuple[int, int] | None = None):
        if base_dir is None:
            # Locate relative to ui directory
            self.base_dir = pathlib.Path(__file__).parent.parent
        else:
            self.base_dir = pathlib.Path(base_dir)
            
        self.piece_size = piece_size
        self.board_size = board_size
        self.board_bg: Img | None = None
        # Cache containing PieceAsset objects
        self.pieces: list[PieceAsset] = []

    def load_all(self) -> None:
        """Loads and caches all GUI assets (board background, piece animation configs, and sprites)."""
        self._load_board_background()
        self._load_piece_assets()

    def _load_board_background(self) -> None:
        board_path = self.base_dir / "board.png"
        self.board_bg = Img().read(board_path, size=self.board_size)

    def _load_piece_assets(self) -> None:
        pieces_dir = self.base_dir / "pieces2"
        if not pieces_dir.exists():
            raise FileNotFoundError(f"Pieces directory not found: {pieces_dir}")

        for folder_name in os.listdir(pieces_dir):
            self._load_piece(pieces_dir, folder_name)

    def _load_piece(self, pieces_dir: pathlib.Path, folder_name: str) -> None:
        folder_path = pieces_dir / folder_name
        if not folder_path.is_dir():
            return

        piece_key = self._parse_piece_key(folder_name)
        if piece_key is None:
            return

        states_dir = folder_path / "states"
        if not states_dir.exists():
            return

        for state_name in os.listdir(states_dir):
            self._load_state(piece_key, states_dir, state_name)

    def _parse_piece_key(self, folder_name: str) -> tuple[str, str] | None:
        if len(folder_name) != 2:
            return None
        kind_char = folder_name[0]
        color_char = folder_name[1].lower()
        return (color_char, kind_char)

    def _load_state(self, piece_key: tuple[str, str], states_dir: pathlib.Path, state_name: str) -> None:
        state_path = states_dir / state_name
        if not state_path.is_dir():
            return

        config = self._load_config(state_path)
        sprites = self._load_sprites(state_path)

        color, kind = piece_key
        asset = PieceAsset(
            color=color,
            kind=kind,
            state_name=state_name,
            config=config,
            sprites=sprites
        )
        self.pieces.append(asset)

    def _load_config(self, state_path: pathlib.Path) -> dict:
        config_file = state_path / "config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                return json.load(f)
        return {}

    def _load_sprites(self, state_path: pathlib.Path) -> list[Img]:
        sprites_dir = state_path / "sprites"
        sprite_frames = []
        if sprites_dir.exists():
            sprite_files = self._get_sorted_sprite_files(sprites_dir)
            for file_name in sprite_files:
                sprite_path = sprites_dir / file_name
                frame_img = Img().read(sprite_path, size=self.piece_size)
                sprite_frames.append(frame_img)
        return sprite_frames

    def _get_sorted_sprite_files(self, sprites_dir: pathlib.Path) -> list[str]:
        return sorted(
            [f for f in os.listdir(sprites_dir) if f.endswith(".png")],
            key=lambda x: int(os.path.splitext(x)[0])
        )

    def get_board_background(self) -> Img:
        if self.board_bg is None:
            raise ValueError("Assets not loaded. Call load_all() first.")
        return self.board_bg

    def get_piece_assets(self, color: str, kind: str, state_name: str) -> PieceAsset:
        """Returns the PieceAsset model for the given piece and state."""
        color_lower = color.lower()
        kind_upper = kind.upper()
        for asset in self.pieces:
            if asset.color == color_lower and asset.kind == kind_upper and asset.state_name == state_name:
                return asset
        
        raise KeyError(f"No assets found for piece {color_lower}{kind_upper} in state '{state_name}'")
