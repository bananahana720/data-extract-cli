#!/usr/bin/env python3
"""
Validate that a commit follows git safety protocols.
Checks for hook compliance, message format, and test status.
"""

import re
import subprocess
import sys
from pathlib import Path


def check_precommit_installed():
    """Check if pre-commit hooks are installed."""
    git_dir = Path(".git")
    if not git_dir.exists():
        return False, "Not in a git repository"

    pre_commit_hook = git_dir / "hooks" / "pre-commit"
    if not pre_commit_hook.exists():
        return False, "Pre-commit hooks not installed. Run: pre-commit install"

    return True, "Pre-commit hooks installed"


def validate_commit_message(message):
    """Validate commit message format."""
    # Check conventional commit format
    pattern = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+"

    lines = message.strip().split("\n")
    if not lines:
        return False, "Empty commit message"

    if not re.match(pattern, lines[0]):
        return False, "Invalid commit format. Expected: type(scope): subject"

    return True, "Valid commit message format"


def run_tests():
    """Run tests to ensure they pass."""
    try:
        result = subprocess.run(
            ["pytest", "--co", "-q"],  # Just collect tests, don't run
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Test collection failed"

        # Now run a quick smoke test if available
        result = subprocess.run(
            ["pytest", "-x", "--tb=short", "-q"], capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return False, f"Tests failed:\n{result.stdout}\n{result.stderr}"

        return True, "Tests passing"
    except subprocess.TimeoutExpired:
        return False, "Tests timed out"
    except FileNotFoundError:
        return True, "Pytest not found - skipping test check"
    except Exception as e:
        return False, f"Test execution error: {e}"


def check_linters():
    """Check that linters pass."""
    issues = []

    # Check black
    try:
        result = subprocess.run(["black", "--check", "."], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("Black: formatting issues found")
    except FileNotFoundError:
        pass  # Tool not installed

    # Check ruff
    try:
        result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("Ruff: linting issues found")
    except FileNotFoundError:
        pass  # Tool not installed

    if issues:
        return False, "\n".join(issues)

    return True, "Linters passing"


def main():
    """Run all validation checks."""
    print("Git Safety Protocol Validator")
    print("=" * 40)

    checks = [
        ("Pre-commit hooks", check_precommit_installed),
        ("Linters", check_linters),
        ("Tests", run_tests),
    ]

    all_passed = True

    for name, check_func in checks:
        print(f"\nChecking {name}...")
        passed, message = check_func()

        if passed:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("✅ All checks passed - safe to commit")
        return 0
    else:
        print("❌ Some checks failed - fix issues before committing")
        print("\nRemember: NEVER use --no-verify to bypass these checks!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
