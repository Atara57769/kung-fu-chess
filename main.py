import sys
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError
from engine.controller import Controller
from engine.game_engine import GameEngine


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


def execute_commands(board, commands, controller_class=None, board_service_class=None, stdout=sys.stdout):
    """Executes parsed commands against the initialized board using Controller."""
    from models.game_state import GameState

    state = GameState(board=board)
    game_engine = GameEngine()

    if controller_class is not None:
        controller = controller_class(state, game_engine, stdout)
    else:
        controller = Controller(state, game_engine, stdout)

    def handle_print(parts):
        if parts == ["print", "board"]:
            controller.print_board()

    def handle_click(parts):
        if len(parts) == 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                controller.click(x, y)
            except ValueError:
                pass

    def handle_wait(parts):
        if len(parts) == 2:
            try:
                ms = int(parts[1])
                controller.wait(ms)
            except ValueError:
                pass

    def handle_jump(parts):
        if len(parts) == 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                controller.jump(x, y)
            except ValueError:
                pass

    command_handlers = {
        "print": handle_print,
        "click": handle_click,
        "wait": handle_wait,
        "jump": handle_jump,
    }

    for cmd in commands:
        parts = cmd.split()
        if not parts:
            continue
        handler = command_handlers.get(parts[0])
        if handler:
            handler(parts)


def main(stdin=sys.stdin, stdout=sys.stdout, exit_fn=sys.exit, board_parser=None,
         board_service_class=None):
    """Main orchestration flow of parsing, validating, and executing commands."""
    lines = read_input_lines(stdin)
    board_start, commands_start = find_section_indices(lines)

    if board_start == -1:
        return

    board_lines = extract_board_lines(lines, board_start, commands_start)
    commands = extract_command_lines(lines, commands_start)

    if board_parser is None:
        from services.board_parser import TextBoardParser
        board_parser = TextBoardParser()

    try:
        board = board_parser.parse(board_lines)
    except UnknownTokenError:
        print("ERROR UNKNOWN_TOKEN", file=stdout)
        exit_fn(0)
        return
    except RowWidthMismatchError:
        print("ERROR ROW_WIDTH_MISMATCH", file=stdout)
        exit_fn(0)
        return

    execute_commands(board, commands, stdout=stdout)


if __name__ == "__main__":
    main()
