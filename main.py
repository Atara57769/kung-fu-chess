import sys
from models.board import Board
from exceptions import UnknownTokenError, RowWidthMismatchError
from services.board_service import boardService


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
    if board_service_class is boardService:
        from services.jump_service import JumpService
        from services.move_scheduler import MoveScheduler
        from services.move_validation_service import MoveValidationService

        jump_service = JumpService()
        scheduler = MoveScheduler(board, jump_service)
        validation = MoveValidationService(board, scheduler)

        service = boardService(
            board=board,
            stdout=stdout,
            move_scheduler=scheduler,
            move_validation_service=validation,
            jump_service=jump_service,
        )
    else:
        service = board_service_class(board, stdout=stdout)
    def handle_print(parts):
        if parts == ["print", "board"]:
            service.print_board()

    def handle_click(parts):
        if len(parts) == 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                service.click(x, y)
            except ValueError:
                pass

    def handle_wait(parts):
        if len(parts) == 2:
            try:
                ms = int(parts[1])
                service.wait(ms)
            except ValueError:
                pass

    def handle_jump(parts):
        if len(parts) == 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                service.jump(x, y)
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
