#!/usr/bin/env python3
"""Add test IDs to P0 tests for traceability.

This script automatically adds @pytest.mark.test_id markers to P0 tests
based on their story number and sequence.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def extract_story_from_path(file_path: Path) -> str:
    """Extract story identifier from file path.

    Examples:
        test_story_5_1/test_foo.py -> "5.1"
        data_extract/core/test_models.py -> "core"
    """
    path_str = str(file_path)

    # Check for story-specific directories
    story_match = re.search(r"test_story_(\d+)_(\d+)", path_str)
    if story_match:
        return f"{story_match.group(1)}.{story_match.group(2)}"

    # Core infrastructure tests
    if "data_extract/core" in path_str:
        return "core"

    # Integration tests
    if "integration" in path_str:
        return "int"

    return "misc"


def determine_test_type(file_path: Path, content: str) -> str:
    """Determine test type from file path and content.

    Returns: UNIT, INT, BEH, UAT, or PERF
    """
    if "integration" in str(file_path):
        return "INT"

    # Check markers in content
    if "pytest.mark.behavioral" in content:
        return "BEH"
    if "pytest.mark.uat" in content:
        return "UAT"
    if "pytest.mark.performance" in content:
        return "PERF"

    return "UNIT"


def find_test_functions(content: str) -> List[Tuple[int, str]]:
    """Find all test function definitions in content.

    Returns list of (line_number, function_name) tuples.
    """
    functions = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Match test function definitions
        match = re.match(r"^\s*def (test_\w+)\(", line)
        if match:
            functions.append((i, match.group(1)))

    return functions


def has_test_id_marker(content: str, line_num: int) -> bool:
    """Check if test function already has test_id marker."""
    lines = content.split("\n")

    # Check 5 lines before the function definition
    start = max(0, line_num - 6)
    end = line_num - 1

    for i in range(start, end):
        if i < len(lines) and "@pytest.mark.test_id" in lines[i]:
            return True

    return False


def add_test_id_to_function(content: str, line_num: int, test_id: str) -> str:
    """Add test_id marker to a test function.

    Args:
        content: File content
        line_num: Line number of function definition (1-indexed)
        test_id: Test ID to add (e.g., "5.1-UNIT-001")

    Returns:
        Updated content
    """
    lines = content.split("\n")

    # Find the indentation of the function definition
    func_line = lines[line_num - 1]
    indent = len(func_line) - len(func_line.lstrip())

    # Create the marker with correct indentation
    marker = " " * indent + f'@pytest.mark.test_id("{test_id}")'

    # Insert marker before function definition
    lines.insert(line_num - 1, marker)

    return "\n".join(lines)


def process_file(file_path: Path, dry_run: bool = False) -> Dict[str, any]:
    """Process a single test file to add test IDs.

    Args:
        file_path: Path to test file
        dry_run: If True, don't write changes

    Returns:
        Dictionary with processing statistics
    """
    content = file_path.read_text()

    # Check if file has P0 marker
    if "pytest.mark.P0" not in content:
        return {
            "file": str(file_path),
            "skipped": True,
            "reason": "Not P0",
            "ids_added": 0,
        }

    # Extract story and test type
    story = extract_story_from_path(file_path)
    test_type = determine_test_type(file_path, content)

    # Find all test functions
    test_functions = find_test_functions(content)

    # Track modifications
    modified_content = content
    sequence = 1
    ids_added = 0
    offset = 0  # Track line offset from insertions

    for line_num, func_name in test_functions:
        # Adjust line number for previous insertions
        adjusted_line = line_num + offset

        # Skip if already has test_id
        if has_test_id_marker(modified_content, adjusted_line):
            continue

        # Create test ID
        test_id = f"{story}-{test_type}-{sequence:03d}"

        # Add marker
        modified_content = add_test_id_to_function(modified_content, adjusted_line, test_id)

        ids_added += 1
        sequence += 1
        offset += 1  # One line added

    # Write changes if not dry run and changes were made
    if not dry_run and ids_added > 0:
        file_path.write_text(modified_content)

    return {
        "file": str(file_path),
        "skipped": False,
        "story": story,
        "test_type": test_type,
        "total_tests": len(test_functions),
        "ids_added": ids_added,
        "first_id": f"{story}-{test_type}-001" if ids_added > 0 else None,
        "last_id": f"{story}-{test_type}-{ids_added:03d}" if ids_added > 0 else None,
    }


def process_file_with_sequence(
    file_path: Path, start_sequence: int, dry_run: bool = False
) -> Dict[str, any]:
    """Process a single test file with global sequence numbering.

    Args:
        file_path: Path to test file
        start_sequence: Starting sequence number for this file
        dry_run: If True, don't write changes

    Returns:
        Dictionary with processing statistics including next_sequence
    """
    content = file_path.read_text()

    # Check if file has P0 marker
    if "pytest.mark.P0" not in content:
        return {
            "file": str(file_path),
            "skipped": True,
            "reason": "Not P0",
            "ids_added": 0,
            "next_sequence": start_sequence,
        }

    # Extract story and test type
    story = extract_story_from_path(file_path)
    test_type = determine_test_type(file_path, content)

    # Find all test functions
    test_functions = find_test_functions(content)

    # Track modifications
    modified_content = content
    sequence = start_sequence
    ids_added = 0
    offset = 0  # Track line offset from insertions
    first_id = None
    last_id = None

    for line_num, func_name in test_functions:
        # Adjust line number for previous insertions
        adjusted_line = line_num + offset

        # Skip if already has test_id
        if has_test_id_marker(modified_content, adjusted_line):
            # Still need to increment sequence for existing IDs
            sequence += 1
            continue

        # Create test ID with global sequence
        test_id = f"{story}-{test_type}-{sequence:03d}"

        if first_id is None:
            first_id = test_id
        last_id = test_id

        # Add marker
        modified_content = add_test_id_to_function(modified_content, adjusted_line, test_id)

        ids_added += 1
        sequence += 1
        offset += 1  # One line added

    # Write changes if not dry run and changes were made
    if not dry_run and ids_added > 0:
        file_path.write_text(modified_content)

    return {
        "file": str(file_path),
        "skipped": False,
        "story": story,
        "test_type": test_type,
        "total_tests": len(test_functions),
        "ids_added": ids_added,
        "first_id": first_id,
        "last_id": last_id,
        "next_sequence": sequence,  # For next file in same story-type group
    }


def main():
    """Process all P0 test files."""
    # Parse arguments
    dry_run = "--dry-run" in sys.argv

    # Define critical test directories
    test_dirs = [
        "tests/unit/test_cli/test_story_5_1",
        "tests/unit/test_cli/test_story_5_6",
        "tests/unit/data_extract/core",
        "tests/integration",
    ]

    project_root = Path(__file__).parent.parent

    # Collect all test files
    test_files = []
    for test_dir in test_dirs:
        dir_path = project_root / test_dir
        if dir_path.exists():
            test_files.extend(dir_path.rglob("test_*.py"))

    # Sort for consistent processing
    test_files = sorted(set(test_files))

    # Group files by story for global sequence numbering
    files_by_story = {}
    for file_path in test_files:
        content = file_path.read_text()
        if "pytest.mark.P0" not in content:
            continue

        story = extract_story_from_path(file_path)
        test_type = determine_test_type(file_path, content)
        key = f"{story}-{test_type}"

        if key not in files_by_story:
            files_by_story[key] = []
        files_by_story[key].append(file_path)

    print(f"Found {len(test_files)} test files")
    print(f"P0 files by story-type: {len(files_by_story)} groups")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("-" * 80)

    # Process each story-type group with global sequence
    results = []
    for story_type_key in sorted(files_by_story.keys()):
        files = files_by_story[story_type_key]
        global_sequence = 1

        for file_path in files:
            result = process_file_with_sequence(file_path, global_sequence, dry_run=dry_run)
            results.append(result)

            if not result["skipped"] and result["ids_added"] > 0:
                print(f"\n✓ {result['file']}")
                print(f"  Story: {result['story']} | Type: {result['test_type']}")
                print(f"  Added {result['ids_added']}/{result['total_tests']} test IDs")
                print(f"  Range: {result['first_id']} to {result['last_id']}")
                global_sequence = result["next_sequence"]

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    processed = [r for r in results if not r["skipped"]]
    skipped = [r for r in results if r["skipped"]]

    total_ids_added = sum(r["ids_added"] for r in processed)

    print(f"\nProcessed: {len(processed)} files")
    print(f"Skipped: {len(skipped)} files")
    print(f"Total test IDs added: {total_ids_added}")

    # Group by story
    by_story: Dict[str, int] = {}
    for r in processed:
        if r["ids_added"] > 0:
            story = r["story"]
            by_story[story] = by_story.get(story, 0) + r["ids_added"]

    if by_story:
        print("\nTest IDs by Story:")
        for story in sorted(by_story.keys()):
            print(f"  {story}: {by_story[story]} test IDs")

    if dry_run:
        print("\n⚠️  DRY RUN - No files were modified")
        print("Run without --dry-run to apply changes")
    else:
        print("\n✓ Changes written to files")


if __name__ == "__main__":
    main()
