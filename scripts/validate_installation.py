#!/usr/bin/env python3
"""Installation validation for current CLI/UI command surface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


TestFn = Callable[[], bool]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UI_HOME = PROJECT_ROOT / ".ui-home"
DEFAULT_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"


def _resolve_python() -> str:
    if DEFAULT_PYTHON.exists():
        return str(DEFAULT_PYTHON)
    return sys.executable


PYTHON_EXE = _resolve_python()


def print_header(message: str) -> None:
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def ok(message: str) -> None:
    print(f"{GREEN}PASS{RESET} {message}")


def fail(message: str) -> None:
    print(f"{RED}FAIL{RESET} {message}")


def run(cmd: list[str], expect_success: bool = True) -> tuple[bool, str, str]:
    env = dict(os.environ)
    env.setdefault("DATA_EXTRACT_UI_HOME", str(DEFAULT_UI_HOME))
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=PROJECT_ROOT,
            env=env,
        )
    except Exception as exc:
        return False, "", str(exc)

    success = (completed.returncode == 0) == expect_success
    return success, completed.stdout, completed.stderr


def assert_contains(output: str, expected: str) -> bool:
    return expected.lower() in output.lower()


def cli_cmd(*args: str) -> list[str]:
    return [PYTHON_EXE, "-m", "data_extract", *args]


def test_help() -> bool:
    success, stdout, stderr = run(cli_cmd("--help"))
    if success and all(assert_contains(stdout, token) for token in ["process", "status", "retry"]):
        ok("data-extract --help")
        return True
    fail(f"data-extract --help failed: {stderr[:200]}")
    return False


def test_version() -> bool:
    success, stdout, stderr = run(cli_cmd("--version"))
    if success and assert_contains(stdout, "Data Extraction Tool"):
        ok("data-extract --version")
        return True
    fail(f"data-extract --version failed: {stderr[:200]}")
    return False


def test_command_help(command: str) -> bool:
    success, _, stderr = run(cli_cmd(command, "--help"))
    if success:
        ok(f"data-extract {command} --help")
        return True
    fail(f"data-extract {command} --help failed: {stderr[:200]}")
    return False


def test_process_and_status() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "inputs"
        output = tmp / "outputs"
        source.mkdir(parents=True, exist_ok=True)
        (source / "sample.txt").write_text("alpha beta gamma", encoding="utf-8")

        process_cmd = [
            *cli_cmd(
                "process",
                str(source),
                "--output",
                str(output),
                "--format",
                "json",
                "--non-interactive",
            ),
        ]
        success, _, stderr = run(process_cmd)
        if not success:
            fail(f"process command failed: {stderr[:200]}")
            return False

        expected = output / "sample.json"
        if not expected.exists():
            fail("process command did not create sample.json")
            return False

        status_cmd = [
            *cli_cmd(
                "status",
                str(source),
                "--output",
                str(output),
                "--json",
            ),
        ]
        success, stdout, stderr = run(status_cmd)
        if not success:
            fail(f"status command failed: {stderr[:200]}")
            return False

        try:
            payload = json.loads(stdout)
            if "sync_state" not in payload:
                raise ValueError("Missing sync_state")
        except Exception as exc:
            fail(f"status JSON output invalid: {exc}")
            return False

        ok("process + status workflow")
        return True


def test_ui_check() -> bool:
    success, _, stderr = run(cli_cmd("ui", "--check"))
    if success:
        ok("data-extract ui --check")
        return True
    fail(f"data-extract ui --check failed: {stderr[:200]}")
    return False


def main() -> int:
    print_header("Data Extract Installation Validation")

    tests: list[TestFn] = [
        test_help,
        test_version,
        lambda: test_command_help("process"),
        lambda: test_command_help("retry"),
        lambda: test_command_help("status"),
        lambda: test_command_help("config"),
        test_process_and_status,
        test_ui_check,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as exc:
            fail(f"Unhandled test exception: {exc}")

    total = len(tests)
    print_header("Validation Summary")
    print(f"Passed: {passed}/{total}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
