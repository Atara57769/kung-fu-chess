import sys
from shared.logger_config import setup_logging
from server.game.services.script_runner import ScriptRunner


def main(stdin=sys.stdin, stdout=sys.stdout, exit_fn=sys.exit):
    """Main orchestration flow of parsing, validating, and executing commands."""
    setup_logging()
    runner = ScriptRunner(stdin=stdin, stdout=stdout, exit_fn=exit_fn)
    runner.run()


if __name__ == "__main__":
    main()
