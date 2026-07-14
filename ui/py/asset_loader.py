import os
import json
import pathlib
from img import Img
from constants import CELL_SIZE

class AssetLoader:
    def __init__(self, base_dir: str | pathlib.Path = None, piece_size: tuple[int, int] = (CELL_SIZE, CELL_SIZE)):
        if base_dir is None:
            # Locate relative to c:\Users\m0258\OneDrive\Desktop\ctd\ui
            self.base_dir = pathlib.Path(__file__).parent.parent
        else:
            self.base_dir = pathlib.Path(base_dir)
            
        self.piece_size = piece_size
        self.board_bg: Img | None = None
        # Cache structured as: self.pieces[(color, kind)][state_name] = { "config": config_dict, "sprites": list[Img] }
        self.pieces: dict[tuple[str, str], dict[str, dict]] = {}

    def load_all(self) -> None:
        """Loads and caches all GUI assets (board background, piece animation configs, and sprites)."""
        # 1. Load Board Background
        board_path = self.base_dir / "board.png"
        self.board_bg = Img().read(board_path)

        # 2. Load Pieces
        pieces_dir = self.base_dir / "pieces2"
        if not pieces_dir.exists():
            raise FileNotFoundError(f"Pieces directory not found: {pieces_dir}")

        for folder_name in os.listdir(pieces_dir):
            folder_path = pieces_dir / folder_name
            if not folder_path.is_dir():
                continue

            # Parse piece kind and color from directory name (e.g., 'QW' -> kind='Q', color='w')
            if len(folder_name) != 2:
                continue
            kind_char = folder_name[0]  # E.g., 'Q'
            color_char = folder_name[1].lower()  # E.g., 'w' or 'b'
            piece_key = (color_char, kind_char)

            self.pieces[piece_key] = {}

            states_dir = folder_path / "states"
            if not states_dir.exists():
                continue

            for state_name in os.listdir(states_dir):
                state_path = states_dir / state_name
                if not state_path.is_dir():
                    continue

                # Load config.json
                config_file = state_path / "config.json"
                if config_file.exists():
                    with open(config_file, "r") as f:
                        config = json.load(f)
                else:
                    config = {}

                # Load sprite frames
                sprites_dir = state_path / "sprites"
                sprite_frames = []
                if sprites_dir.exists():
                    # Sort files numerically so 1.png, 2.png, 10.png play in order
                    sprite_files = sorted(
                        [f for f in os.listdir(sprites_dir) if f.endswith(".png")],
                        key=lambda x: int(os.path.splitext(x)[0])
                    )
                    for file_name in sprite_files:
                        sprite_path = sprites_dir / file_name
                        # Pre-read and resize to the configured piece size
                        frame_img = Img().read(sprite_path, size=self.piece_size)
                        sprite_frames.append(frame_img)

                self.pieces[piece_key][state_name] = {
                    "config": config,
                    "sprites": sprite_frames
                }

    def get_board_background(self) -> Img:
        if self.board_bg is None:
            raise ValueError("Assets not loaded. Call load_all() first.")
        return self.board_bg

    def get_piece_assets(self, color: str, kind: str, state_name: str) -> dict:
        """Returns the config and preloaded Img frames for the given piece and state."""
        piece_key = (color.lower(), kind.upper())
        if piece_key not in self.pieces:
            raise KeyError(f"No assets found for piece key: {piece_key}")
        
        state_dict = self.pieces[piece_key].get(state_name)
        if not state_dict:
            raise KeyError(f"No assets found for piece {piece_key} in state '{state_name}'")
        
        return state_dict
