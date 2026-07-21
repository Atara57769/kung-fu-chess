import sys
import logging
from shared.exceptions import UnknownTokenError, RowWidthMismatchError
from server.game.services.board_parser import TextBoardParser
from shared.models.game_state import GameState
from server.game.engine.game_engine import GameEngine
from server.game.engine.controller import Controller
from shared.models.cell import Cell
from shared.constants import CELL_SIZE

logger = logging.getLogger(__name__)


class ScriptRunner:
    def __init__(self, stdin=sys.stdin, stdout=sys.stdout, exit_fn=sys.exit):
        self.stdin = stdin
        self.stdout = stdout
        self.exit_fn = exit_fn

    def _read_input_lines(self):
        """Reads lines from standard input and strips surrounding whitespace."""
        try:
            input_data = self.stdin.read()
        except KeyboardInterrupt:
            return []
        return [line.strip() for line in input_data.splitlines()]

    def _find_section_indices(self, lines):
        """Locates the starting indices of the Board and Commands sections."""
        board_start = -1
        commands_start = -1
        for i, line in enumerate(lines):
            if line == "Board:":
                board_start = i
            elif line == "Commands:":
                commands_start = i
        return board_start, commands_start

    def _extract_board_lines(self, lines, board_start, commands_start):
        """Extracts and filters board configuration lines from the input."""
        if board_start == -1:
            return []
        if commands_start != -1:
            board_lines_raw = lines[board_start + 1 : commands_start]
        else:
            board_lines_raw = lines[board_start + 1 :]
        return [l for l in board_lines_raw if l]

    def _extract_command_lines(self, lines, commands_start):
        """Extracts active command lines from the input."""
        if commands_start == -1:
            return []
        return [cmd for cmd in lines[commands_start + 1 :] if cmd]

    def _pixel_to_cell(self, board, x: int, y: int) -> Cell | None:
        if x < 0 or y < 0:
            return None
        cell_y = y // CELL_SIZE
        cell_x = x // CELL_SIZE
        if 0 <= cell_x < board.width and 0 <= cell_y < board.height:
            return Cell(cell_y, cell_x)
        return None

    def _execute_commands(self, board, commands):
        """Executes parsed commands against the initialized board using Controller."""
        state = GameState(board=board)
        game_engine = GameEngine()
        controller = Controller(state, game_engine, self.stdout)

        def handle_print(parts):
            if parts == ["print", "board"]:
                controller.print_board()

        def handle_click(parts):
            if len(parts) == 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    cell = self._pixel_to_cell(board, x, y)
                    controller.click(cell)
                except ValueError:
                    logger.warning(f"Invalid click coordinates: {parts[1:]}")

        def handle_wait(parts):
            if len(parts) == 2:
                try:
                    ms = int(parts[1])
                    controller.wait(ms)
                except ValueError:
                    logger.warning(f"Invalid wait duration: {parts[1]}")

        def handle_jump(parts):
            if len(parts) == 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    cell = self._pixel_to_cell(board, x, y)
                    controller.jump(cell)
                except ValueError:
                    logger.warning(f"Invalid jump coordinates: {parts[1:]}")

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
            else:
                logger.warning(f"Unknown command: {parts[0]}")

    def run(self):
        """Main orchestration flow of parsing, validating, and executing commands."""
        lines = self._read_input_lines()
        board_start, commands_start = self._find_section_indices(lines)

        if board_start == -1:
            logger.error("No Board section found in input.")
            return

        board_lines = self._extract_board_lines(lines, board_start, commands_start)
        commands = self._extract_command_lines(lines, commands_start)

        board_parser = TextBoardParser()

        try:
            board = board_parser.parse(board_lines)
        except UnknownTokenError:
            logger.error("Failed to parse board: Unknown token encountered.")
            print("ERROR UNKNOWN_TOKEN", file=self.stdout)
            self.exit_fn(0)
            return
        except RowWidthMismatchError:
            logger.error("Failed to parse board: Row width mismatch.")
            print("ERROR ROW_WIDTH_MISMATCH", file=self.stdout)
            self.exit_fn(0)
            return

        self._execute_commands(board, commands)
