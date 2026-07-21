import os
import subprocess
import sys
import textwrap
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

EXPECTED_OUTPUTS = {
    "board_parsing.kfc": """
        wK . bQ
        . wN .
        bP . wR
    """,
    "click_to_move.kfc": """
        . . .
        . wK .
        . . .
    """,
    "rook_moves.kfc": """
        . . wR
    """,
    "invalid_moves.kfc": """
        wR . .
        . . .
        . . .
    """,
    "capture.kfc": """
        . . wR
    """,
    "game_over.kfc": """
        . wK
    """
}

def normalize(text):
    return "\n".join(
        line.rstrip()
        for line in textwrap.dedent(text).strip().splitlines()
    )

@pytest.mark.parametrize("script_name", list(EXPECTED_OUTPUTS.keys()))
def test_kfc_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    assert os.path.exists(script_path), f"Script {script_name} not found at {script_path}"
    
    with open(script_path, "r", encoding="utf-8") as f:
        input_data = f.read()

    import io
    from main import main as main_func

    stdin = io.StringIO(input_data)
    stdout = io.StringIO()

    # Pass a dummy exit function so it doesn't terminate the pytest process
    main_func(stdin=stdin, stdout=stdout, exit_fn=lambda code: None)
    
    output = normalize(stdout.getvalue())
    expected = normalize(EXPECTED_OUTPUTS[script_name])
    
    assert output == expected

