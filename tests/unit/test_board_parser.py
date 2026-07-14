import pytest
import io
from services.board_parser import TextBoardParser
from exceptions import UnknownTokenError, RowWidthMismatchError
from models.pieces import Piece
from models.cell import Cell
from main import main as main_func
from runners.script_runner import ScriptRunner


def test_board_parser_valid():
    lines = [
        "wK . bP",
        ". wQ .",
        "wN bB wP"
    ]
    board = TextBoardParser().parse(lines)
    assert board.width == 3
    assert board.height == 3
    assert len(board.grid) == 3
    assert board.grid[0] == [Piece("w", "K", Cell(0, 0)), None, Piece("b", "P", Cell(0, 2))]
    assert board.grid[1] == [None, Piece("w", "Q", Cell(1, 1)), None]
    assert board.grid[2] == [Piece("w", "N", Cell(2, 0)), Piece("b", "B", Cell(2, 1)), Piece("w", "P", Cell(2, 2))]


def test_board_parser_empty():
    board = TextBoardParser().parse([])
    assert board.width == 0
    assert board.height == 0
    assert board.grid == []


def test_board_parser_unknown_token():
    with pytest.raises(UnknownTokenError):
        TextBoardParser().parse(["wK . xP"])
    with pytest.raises(UnknownTokenError):
        TextBoardParser().parse(["wK . wK2"])
    with pytest.raises(UnknownTokenError):
        TextBoardParser().parse(["wK . zP"])
    with pytest.raises(UnknownTokenError):
        TextBoardParser().parse(["wK . wZ"])


def test_board_parser_row_width_mismatch():
    with pytest.raises(RowWidthMismatchError):
        TextBoardParser().parse(["wK .", "bP . bB ."])


def test_read_input_lines_normal():
    stdin = io.StringIO("  line1  \n  line2\n")
    runner = ScriptRunner(stdin=stdin)
    assert runner._read_input_lines() == ["line1", "line2"]


def test_read_input_lines_interrupt():
    class InterruptingStdin:
        def read(self):
            raise KeyboardInterrupt()
    runner = ScriptRunner(stdin=InterruptingStdin())
    assert runner._read_input_lines() == []


def test_find_section_indices():
    runner = ScriptRunner()
    lines = ["Other", "Board:", "wK .", "Commands:", "print board"]
    board_start, commands_start = runner._find_section_indices(lines)
    assert board_start == 1
    assert commands_start == 3

    lines_missing = ["Other"]
    assert runner._find_section_indices(lines_missing) == (-1, -1)


def test_extract_board_lines():
    runner = ScriptRunner()
    lines = ["Board:", "wK .", "Commands:", "print board"]
    # Case with commands
    assert runner._extract_board_lines(lines, 0, 2) == ["wK ."]
    # Case without commands
    assert runner._extract_board_lines(lines, 0, -1) == ["wK .", "Commands:", "print board"]
    # Case with no board_start
    assert runner._extract_board_lines(lines, -1, 2) == []


def test_extract_command_lines():
    runner = ScriptRunner()
    lines = ["Board:", "wK .", "Commands:", "print board", ""]
    # Case with commands_start
    assert runner._extract_command_lines(lines, 2) == ["print board"]
    # Case without commands_start
    assert runner._extract_command_lines(lines, -1) == []


def test_execute_commands_edge_cases():
    runner = ScriptRunner()
    board = TextBoardParser().parse(["wP .", ". ."])
    
    commands = [
        "click abc 200",
        "click 100",
        "wait xyz",
        "wait 500 600",
        "jump pqr 400",
        "jump 300",
        "jump 100 100",  # valid jump command to cover lines 84-85
        "unknown_cmd",
        "",
        "   "
    ]
    runner._execute_commands(board, commands)  # Should execute without errors


def test_main_missing_board():
    stdin = io.StringIO("Commands:\nprint board\n")
    out = io.StringIO()
    main_func(stdin=stdin, stdout=out)
    assert out.getvalue() == ""


def test_main_unknown_token_error():
    stdin = io.StringIO("Board:\nwK . xP\n")
    out = io.StringIO()
    exited = []
    def exit_fn(code):
        exited.append(code)

    main_func(stdin=stdin, stdout=out, exit_fn=exit_fn)
    assert exited == [0]
    assert "ERROR UNKNOWN_TOKEN" in out.getvalue()


def test_main_row_width_mismatch_error():
    stdin = io.StringIO("Board:\nwK .\nbP . .\n")
    out = io.StringIO()
    exited = []
    def exit_fn(code):
        exited.append(code)

    main_func(stdin=stdin, stdout=out, exit_fn=exit_fn)
    assert exited == [0]
    assert "ERROR ROW_WIDTH_MISMATCH" in out.getvalue()
