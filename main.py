import sys
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError
from board_service import boardService


def read_input_lines(stdin=sys.stdin):
    """Reads lines from standard input and strips surrounding whitespace."""
    try:
        input_data = stdin.read()
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


def execute_commands(board, commands, board_service_class=boardService, stdout=sys.stdout):
    """Executes parsed commands against the initialized board using boardService."""
    service = board_service_class(board, stdout=stdout)
    for cmd in commands:
        if cmd == "print board":
            service.print_board()
        elif cmd.startswith("click "):
            parts = cmd.split()
            if len(parts) == 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    service.click(x, y)
                except ValueError:
                    pass
        elif cmd.startswith("wait "):
            parts = cmd.split()
            if len(parts) == 2:
                try:
                    ms = int(parts[1])
                    service.wait(ms)
                except ValueError:
                    pass
        elif cmd.startswith("jump "):
            parts = cmd.split()
            if len(parts) == 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    service.jump(x, y)
                except ValueError:
                    pass


def main(stdin=sys.stdin, stdout=sys.stdout, exit_fn=sys.exit, board_class=Board, board_service_class=boardService):
    """Main orchestration flow of parsing, validating, and executing commands."""
    lines = read_input_lines(stdin)
    board_start, commands_start = find_section_indices(lines)
    
    if board_start == -1:
        return

    board_lines = extract_board_lines(lines, board_start, commands_start)
    commands = extract_command_lines(lines, commands_start)

    try:
        board = board_class(board_lines)
    except UnknownTokenError:
        print("ERROR UNKNOWN_TOKEN", file=stdout)
        exit_fn(0)
        return
    except RowWidthMismatchError:
        print("ERROR ROW_WIDTH_MISMATCH", file=stdout)
        exit_fn(0)
        return

    execute_commands(board, commands, board_service_class=board_service_class, stdout=stdout)


if __name__ == "__main__":
    main()
