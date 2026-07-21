import pytest
import sys
import argparse
from unittest.mock import MagicMock, patch
from shared.models.cell import Cell
from shared.models.game_snapshot import GameSnapshot
from client.ui.app.ui_app import parse_board_file, main
from client.ui.app.ui_runner import UIRunner

def test_parse_board_file(tmp_path):
    board_file = tmp_path / "custom_board.txt"
    board_file.write_text("Board:\n. .\nwP bK\n")
    board = parse_board_file(str(board_file))
    assert board.width == 2
    assert board.height == 2
    assert board.get_piece_at(Cell(1, 0)).kind == "P"
    assert board.get_piece_at(Cell(1, 1)).kind == "K"

@patch("client.ui.app.ui_app.AssetLoader")
@patch("client.ui.app.ui_app.Window")
@patch("client.ui.app.ui_app.UIRunner")
def test_main_default_args(mock_runner_cls, mock_window_cls, mock_asset_loader_cls):
    mock_args = argparse.Namespace(board=None, scale=1.0, cell_size=None)
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        main()
    
    mock_asset_loader_cls.assert_called_once()
    mock_runner_cls.assert_called_once()
    mock_runner_cls.return_value.start_loop.assert_called_once()
    mock_window_cls.return_value.close.assert_called_once()

@patch("client.ui.app.ui_app.AssetLoader")
@patch("client.ui.app.ui_app.Window")
@patch("client.ui.app.ui_app.UIRunner")
def test_main_custom_board_and_cell_size(mock_runner_cls, mock_window_cls, mock_asset_loader_cls, tmp_path):
    board_file = tmp_path / "board.txt"
    board_file.write_text("wK .\n. .")
    
    mock_args = argparse.Namespace(board=str(board_file), scale=1.0, cell_size=80)
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        main()
        
    mock_asset_loader_cls.assert_called_once_with(piece_size=(80, 80), board_size=(160, 160))

@patch("client.ui.app.ui_app.AssetLoader")
@patch("client.ui.app.ui_app.Window")
@patch("client.ui.app.ui_app.UIRunner")
def test_main_custom_board_invalid_fallback(mock_runner_cls, mock_window_cls, mock_asset_loader_cls):
    mock_args = argparse.Namespace(board="invalid_path.txt", scale=1.5, cell_size=None)
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        main()
    
    mock_asset_loader_cls.assert_called_once()
    mock_runner_cls.assert_called_once()
