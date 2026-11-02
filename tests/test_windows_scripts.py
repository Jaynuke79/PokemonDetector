from pathlib import Path

import pytest

WINDOWS_DIR = Path(__file__).resolve().parents[1] / "windows"
BATCH_FILES = sorted(WINDOWS_DIR.glob("*.bat"))


def block_parsing_problems(script):
    """Find lines cmd.exe would misread inside parenthesized blocks.

    cmd parses a whole block before running it, so an unquoted ")" ends the block
    wherever it appears, and %VAR% expands too early to see changes made inside
    the block and can bring in a ")" from a path such as C:\\Program Files (x86).
    """
    problems = []
    depth = 0
    for number, line in enumerate(script.splitlines(), start=1):
        stripped = line.strip()
        if stripped.upper().startswith(("REM ", "::")):
            continue
        in_quotes = False
        escaped = False
        at_start = True
        for char in stripped:
            if escaped:
                escaped = False
            elif char == "^" and not in_quotes:
                escaped = True
            elif char == '"':
                in_quotes = not in_quotes
            elif not in_quotes and char == ")":
                if depth > 0 and not at_start:
                    problems.append(f"line {number}: ')' ends the block early")
                depth = max(depth - 1, 0)
            elif not in_quotes and char == "(" and stripped.endswith("("):
                depth += 1
            at_start = False
        if depth > 0 and "%" in stripped.replace("%%", ""):
            problems.append(f"line {number}: %VAR% expanded inside a block")
    return problems


@pytest.mark.parametrize("path", BATCH_FILES, ids=lambda path: path.name)
def test_batch_file_blocks_parse_as_intended(path):
    assert block_parsing_problems(path.read_text()) == []


def test_batch_files_are_covered():
    assert {path.name for path in BATCH_FILES} == {
        "build_windows.bat",
        "fix_model_file.bat",
    }


@pytest.mark.parametrize(
    ("script", "problem"),
    [
        ("if x (\n  echo a (1).txt\n)\n", "')' ends the block early"),
        ("if x (\n  echo %CD%\n)\n", "%VAR% expanded inside a block"),
    ],
)
def test_block_check_catches_known_bugs(script, problem):
    assert any(problem in found for found in block_parsing_problems(script))


def test_block_check_accepts_quoted_and_escaped_parens():
    script = 'if x (\n  echo ^(1^)\n  dir "a (1).txt"\n) else (\n  echo b\n)\n'

    assert block_parsing_problems(script) == []


@pytest.mark.parametrize("path", BATCH_FILES, ids=lambda path: path.name)
def test_batch_files_use_crlf(path):
    # On LF files cmd.exe can fail to find goto labels.
    content = path.read_bytes()
    assert content.count(b"\n") == content.count(b"\r\n")
