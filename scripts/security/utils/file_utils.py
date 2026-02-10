"""File utility functions for security scanning."""

import os
from pathlib import Path
from typing import List, Set

from ..config import SCAN_EXTENSIONS, SKIP_DIRS


def find_files_to_scan(
    project_root: Path,
    extensions: Set[str] = SCAN_EXTENSIONS,
    ignore_patterns: Set[str] = None,
) -> List[Path]:
    """Find all files that should be scanned.

    Args:
        project_root: Root directory to scan
        extensions: File extensions to include
        ignore_patterns: Patterns to ignore

    Returns:
        List of file paths to scan
    """
    ignore_patterns = ignore_patterns or set()
    files_to_scan = []

    for root, dirs, files in os.walk(project_root):
        # Remove directories we should skip
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        root_path = Path(root)

        # Check if this directory should be ignored
        try:
            relative_root = root_path.relative_to(project_root)
            root_str = str(relative_root)
            skip_dir = False
            for pattern in ignore_patterns:
                if pattern in root_str or root_str.startswith(pattern):
                    skip_dir = True
                    break
            if skip_dir:
                dirs.clear()  # Don't descend into this directory
                continue
        except ValueError:
            # Outside project root
            continue

        for file_name in files:
            file_path = root_path / file_name

            # Check extension
            if file_path.suffix in extensions or file_path.name in extensions:
                # Check ignore patterns
                try:
                    relative_path = file_path.relative_to(project_root)
                    path_str = str(relative_path)
                    should_skip = False
                    for pattern in ignore_patterns:
                        if pattern in path_str or path_str.startswith(pattern):
                            should_skip = True
                            break
                    if not should_skip:
                        files_to_scan.append(file_path)
                except ValueError:
                    # Outside project root
                    continue

    return files_to_scan
