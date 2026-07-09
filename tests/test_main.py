import pytest
import io
import sys
from exceptions import UnknownTokenError, RowWidthMismatchError
from models.board import Board
from main import (
    read_input_lines,
    find_section_indices,
    extract_board_lines,
    extract_command_lines,
    execute_commands,
    main
)


# Mock controller for testing execute_commands and main
class MockController:
    def __init__(self, state, game_engine, stdout):
        self.state = state
        self.game_engine = game_engine
        self.stdout = stdout
        self.actions = []

    def print_board(self):
        self.actions.append(("print",))

    def click(self, x, y):
        self.actions.append(("click", x, y))

    def wait(self, ms):
        self.actions.append(("wait", ms))

    def jump(self, x, y):
        self.actions.append(("jump", x, y))


def test_read_input_lines_normal():
    stdin = io.StringIO("  line1  \n  line2\n")
    assert read_input_lines(stdin) == ["line1", "line2"]


def test_read_input_lines_interrupt():
    class InterruptingStdin:
        def read(self):
            raise KeyboardInterrupt()

    assert read_input_lines(InterruptingStdin()) == []


def test_find_section_indices():
    lines = ["Other", "Board:", "wK .", "Commands:", "print board"]
    board_start, commands_start = find_section_indices(lines)
    assert board_start == 1
    assert commands_start == 3

    lines_missing = ["Other"]
    assert find_section_indices(lines_missing) == (-1, -1)


def test_extract_board_lines():
    lines = ["Board:", "wK .", "Commands:", "print board"]
    # Case with commands
    assert extract_board_lines(lines, 0, 2) == ["wK ."]
    # Case without commands
    assert extract_board_lines(lines, 0, -1) == ["wK .", "Commands:", "print board"]
    # Case with no board_start
    assert extract_board_lines(lines, -1, 2) == []


def test_extract_command_lines():
    lines = ["Board:", "wK .", "Commands:", "print board", ""]
    # Case with commands_start
    assert extract_command_lines(lines, 2) == ["print board"]
    # Case without commands_start
    assert extract_command_lines(lines, -1) == []


def test_execute_commands():
    board = Board(["wP .", ". ."])
    commands = [
        "print board",
        "click 100 200",
        "click abc 200",   # value error
        "click 100",       # wrong parts length
        "wait 500",
        "wait xyz",        # value error
        "wait 500 600",    # wrong parts length
        "jump 300 400",
        "jump pqr 400",    # value error
        "jump 300",        # wrong parts length
        "unknown_cmd"
    ]

    captured = []

    class CapturingController(MockController):
        pass

    controller_instance = None

    def mock_controller_class(state, game_engine, stdout):
        nonlocal controller_instance
        controller_instance = CapturingController(state, game_engine, stdout)
        return controller_instance

    execute_commands(board, commands, controller_class=mock_controller_class)

    assert controller_instance.actions == [
        ("print",),
        ("click", 100, 200),
        ("wait", 500),
        ("jump", 300, 400)
    ]


def test_execute_commands_default_class():
    board = Board(["wP .", ". ."])
    output = io.StringIO()
    execute_commands(board, ["print board"], stdout=output)
    assert output.getvalue() == "wP .\n. .\n"


def test_main_missing_board():
    stdin = io.StringIO("Commands:\nprint board\n")
    # Should exit early/return without doing anything
    out = io.StringIO()
    main(stdin=stdin, stdout=out)
    assert out.getvalue() == ""


def test_main_unknown_token_error():
    stdin = io.StringIO("Board:\nwK . xP\n")
    out = io.StringIO()
    exited = []
    def exit_fn(code):
        exited.append(code)

    class MockBoardWithUnknownToken:
        def __init__(self, lines):
            raise UnknownTokenError("ERROR UNKNOWN_TOKEN")

    main(stdin=stdin, stdout=out, exit_fn=exit_fn, board_class=MockBoardWithUnknownToken)
    assert exited == [0]
    assert "ERROR UNKNOWN_TOKEN" in out.getvalue()


def test_main_row_width_mismatch_error():
    stdin = io.StringIO("Board:\nwK .\nbP . .\n")
    out = io.StringIO()
    exited = []
    def exit_fn(code):
        exited.append(code)

    class MockBoardWithMismatch:
        def __init__(self, lines):
            raise RowWidthMismatchError("ERROR ROW_WIDTH_MISMATCH")

    main(stdin=stdin, stdout=out, exit_fn=exit_fn, board_class=MockBoardWithMismatch)
    assert exited == [0]
    assert "ERROR ROW_WIDTH_MISMATCH" in out.getvalue()


def test_main_normal_flow():
    stdin = io.StringIO("Board:\nwK .\nCommands:\nprint board\n")
    out = io.StringIO()

    main(stdin=stdin, stdout=out)
    # Default Controller + GameEngine → should print the board
    assert "wK" in out.getvalue()
