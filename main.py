import sys
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError


def read_input_lines():
    """Reads lines from standard input and strips surrounding whitespace."""
    try:
        input_data = sys.stdin.read()
    except KeyboardInterrupt:
        return []
    return [line.strip() for line in input_data.splitlines()]


def find_section_indices(lines):
    """Locates the starting indices of the Board and Commands sections."""
    board_start = -1
    commands_start = -1
    for i, line in enumerate(lines):
        if line == "Board:":
            board_start = i
        elif line == "Commands:":
            commands_start = i
    return board_start, commands_start


def extract_board_lines(lines, board_start, commands_start):
    """Extracts and filters board configuration lines from the input."""
    if board_start == -1:
        return []
    if commands_start != -1:
        board_lines_raw = lines[board_start + 1 : commands_start]
    else:
        board_lines_raw = lines[board_start + 1 :]
    return [l for l in board_lines_raw if l]


def extract_command_lines(lines, commands_start):
    """Extracts active command lines from the input."""
    if commands_start == -1:
        return []
    return [cmd for cmd in lines[commands_start + 1 :] if cmd]


def execute_commands(board, commands):
    """Executes parsed commands against the initialized board."""
    for cmd in commands:
        if cmd == "print board":
            board.print()


def main():
    """Main orchestration flow of parsing, validating, and executing commands."""
    lines = read_input_lines()
    board_start, commands_start = find_section_indices(lines)
    
    if board_start == -1:
        return

    board_lines = extract_board_lines(lines, board_start, commands_start)
    commands = extract_command_lines(lines, commands_start)

    try:
        board = Board(board_lines)
    except UnknownTokenError:
        print("ERROR UNKNOWN_TOKEN")
        sys.exit(0)
    except RowWidthMismatchError:
        print("ERROR ROW_WIDTH_MISMATCH")
        sys.exit(0)

    execute_commands(board, commands)


if __name__ == "__main__":
    main()
