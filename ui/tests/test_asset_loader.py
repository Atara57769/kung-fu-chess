import pytest
import os
import json
import pathlib
from unittest.mock import MagicMock
from ui.assets.asset_loader import AssetLoader, PieceAsset
from ui.rendering.img import Img

def test_piece_asset_initialization():
    asset = PieceAsset(color="w", kind="P", state_name="idle", config={"key": "val"}, sprites=[])
    assert asset.color == "w"
    assert asset.kind == "P"
    assert asset.state_name == "idle"
    assert asset.config == {"key": "val"}
    assert asset.sprites == []

def test_asset_loader_pieces_initialization():
    loader = AssetLoader()
    assert loader.pieces == []
    # Test default base_dir initialization
    assert loader.base_dir == pathlib.Path(__file__).parent.parent

def test_get_piece_assets():
    loader = AssetLoader()
    asset_wp = PieceAsset(color="w", kind="P", state_name="idle", config={"p": 1}, sprites=[])
    asset_bk = PieceAsset(color="b", kind="K", state_name="move", config={"k": 2}, sprites=[])
    
    loader.pieces = [asset_wp, asset_bk]
    
    # Matching (case-insensitive color and uppercase kind check)
    found = loader.get_piece_assets("W", "p", "idle")
    assert found == asset_wp
    
    found2 = loader.get_piece_assets("B", "K", "move")
    assert found2 == asset_bk
    
    # Not found
    with pytest.raises(KeyError):
        loader.get_piece_assets("w", "P", "move")

def test_get_board_background_not_loaded():
    loader = AssetLoader()
    with pytest.raises(ValueError):
        loader.get_board_background()

