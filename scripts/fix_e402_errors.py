#!/usr/bin/env python3
"""
Fix E402 (module level import not at top of file) errors in test files.

These errors occur because test files use sys.path manipulation before imports,
which is an intentional pattern. The fix is to add # noqa: E402 comments.
"""

import re
import subprocess
from pathlib import Path


def get_files_with_e402():
    """Get list of files with E402 errors from ruff."""
    result = subprocess.run(
        ["ruff", "check", "tests/"],
        capture_output=True,
        text=True,
    )

    files_with_errors = set()
    for line in result.stdout.split("\n"):
        if "E402" in line:
            # Extract filename from error line
            match = re.match(r"^([^:]+\.py):\d+:\d+:", line)
            if match:
                files_with_errors.add(match.group(1))

    return sorted(files_with_errors)


def fix_file(filepath: str) -> tuple[int, int]:
    """
    Fix E402 errors in a single file by adding # noqa: E402 comments.

    Returns:
        Tuple of (lines_modified, imports_fixed)
    """
    path = Path(filepath)
    if not path.exists():
        print(f"⚠️  File not found: {filepath}")
        return 0, 0

    content = path.read_text()
    lines = content.split("\n")

    # Find where sys.path.insert() appears
    sys_path_line = -1
    for i, line in enumerate(lines):
        if "sys.path.insert" in line:
            sys_path_line = i
            break

    # If no sys.path manipulation, this file has a different pattern
    if sys_path_line == -1:
        # Check for pytest.mark lines - imports after those need noqa
        pytestmark_line = -1
        for i, line in enumerate(lines):
            if "pytestmark" in line:
                pytestmark_line = i
                break

        if pytestmark_line == -1:
            print(f"⚠️  No sys.path or pytestmark found in {filepath}")
            return 0, 0

        # Add noqa to imports after pytestmark
        modifications = 0
        imports_fixed = 0
        modified_lines = []

        for i, line in enumerate(lines):
            if i > pytestmark_line and line.strip():
                # Check if it's an import line
                stripped = line.strip()
                if (
                    stripped.startswith("from ") or stripped.startswith("import ")
                ) and "# noqa: E402" not in line:
                    # Add noqa comment
                    modified_lines.append(line + "  # noqa: E402")
                    modifications += 1
                    imports_fixed += 1
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        if modifications > 0:
            path.write_text("\n".join(modified_lines))
            print(f"✓ Fixed {filepath}: {imports_fixed} imports after pytestmark")

        return modifications, imports_fixed

    # Add noqa to imports after sys.path.insert()
    modifications = 0
    imports_fixed = 0
    modified_lines = []

    for i, line in enumerate(lines):
        if i > sys_path_line and line.strip():
            # Check if it's an import line without noqa
            stripped = line.strip()
            if (
                stripped.startswith("from ") or stripped.startswith("import ")
            ) and "# noqa: E402" not in line:
                # Add noqa comment
                modified_lines.append(line + "  # noqa: E402")
                modifications += 1
                imports_fixed += 1
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    if modifications > 0:
        path.write_text("\n".join(modified_lines))
        print(f"✓ Fixed {filepath}: {imports_fixed} imports after sys.path")

    return modifications, imports_fixed


def main():
    """Main entry point."""
    print("Finding files with E402 errors...")
    files = get_files_with_e402()

    if not files:
        print("✓ No E402 errors found!")
        return

    print(f"\nFound {len(files)} files with E402 errors\n")

    total_lines = 0
    total_imports = 0

    for filepath in files:
        lines, imports = fix_file(filepath)
        total_lines += lines
        total_imports += imports

    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Files processed: {len(files)}")
    print(f"  Lines modified: {total_lines}")
    print(f"  Imports fixed: {total_imports}")
    print(f"{'='*60}")

    # Re-run ruff to check remaining errors
    print("\nVerifying fixes...")
    result = subprocess.run(
        ["ruff", "check", "tests/"],
        capture_output=True,
        text=True,
    )

    e402_count = result.stdout.count("E402")
    if e402_count == 0:
        print("✓ All E402 errors fixed!")
    else:
        print(f"⚠️  {e402_count} E402 errors remaining")
        print("\nRemaining errors:")
        for line in result.stdout.split("\n"):
            if "E402" in line:
                print(f"  {line}")


if __name__ == "__main__":
    main()
