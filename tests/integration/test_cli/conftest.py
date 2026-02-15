"""Pytest fixtures for CLI integration tests (Story 5-7).

This module provides fixtures for incremental batch processing integration tests:
- processed_corpus_with_state: A corpus with existing state file
- mixed_corpus: A corpus with new, modified, and unchanged files
- orphan_corpus: A corpus with orphaned output files

Reference: docs/tech-spec-epic-5.md
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = [pytest.mark.P0, pytest.mark.integration]


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents.

    Args:
        file_path: Path to file to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


# ==============================================================================
# Processed Corpus with Existing State
# ==============================================================================


@pytest.fixture
def processed_corpus_with_state(tmp_path: Path) -> dict:
    """
    Create a corpus with existing incremental state file.

    Provides:
    - A source directory with 3-5 pre-processed PDF/TXT files
    - A .data-extract-session/incremental-state.json file containing:
      - version: "1.0"
      - source_dir: path to source directory
      - output_dir: path to output directory
      - processed_at: ISO timestamp
      - files: dict with file hashes and metadata

    This fixture simulates a corpus that has been previously processed,
    allowing tests to verify incremental behavior (skip unchanged files,
    reprocess modified files, etc.).

    Args:
        tmp_path: Pytest built-in temporary directory

    Returns:
        Dictionary with:
        - source_dir: Path to source directory
        - output_dir: Path to output directory
        - state_file: Path to state file
        - file_list: List of file paths in corpus
    """
    # Create directories
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    # Create 3 test files (PDF/TXT mix)
    file_list: list[Path] = []

    # File 1: PDF
    file1 = source_dir / "document_1.pdf"
    file1.write_bytes(b"%PDF-1.4\n" + b"Sample PDF content" * 10)
    file_list.append(file1)

    # File 2: TXT
    file2 = source_dir / "document_2.txt"
    file2.write_text("Sample text document with multiple lines.\n" * 20)
    file_list.append(file2)

    # File 3: PDF
    file3 = source_dir / "document_3.pdf"
    file3.write_bytes(b"%PDF-1.4\n" + b"Another PDF content" * 10)
    file_list.append(file3)

    # Create state file
    now = datetime.now().isoformat()
    files_dict: dict[str, dict] = {}
    state: dict = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "processed_at": now,
        "files": files_dict,
    }

    # Add file entries to state
    for file_path in file_list:
        file_hash = _compute_file_hash(file_path)
        file_size = file_path.stat().st_size

        files_dict[str(file_path)] = {
            "hash": file_hash,
            "processed_at": now,
            "output_path": str(output_dir / f"{file_path.stem}.json"),
            "size_bytes": file_size,
        }

    # Write state file
    session_dir = source_dir.parent / ".data-extract-session"
    session_dir.mkdir(parents=True, exist_ok=True)
    state_file = session_dir / "incremental-state.json"
    state_file.write_text(json.dumps(state, indent=2))

    return {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "file_list": file_list,
    }


# ==============================================================================
# Mixed Corpus (New, Modified, Unchanged Files)
# ==============================================================================


@pytest.fixture
def mixed_corpus(tmp_path: Path) -> dict:
    """
    Create a corpus with mixed file states (new, modified, unchanged).

    Simulates a real-world scenario where:
    - 2 files are unchanged (in state, same hash)
    - 2 files are new (not in state)
    - 1 file is modified (in state, but hash differs)

    This allows tests to verify that incremental processing correctly
    identifies and handles different change types.

    Args:
        tmp_path: Pytest built-in temporary directory

    Returns:
        Dictionary with:
        - source_dir: Path to source directory
        - output_dir: Path to output directory
        - state_file: Path to state file
        - unchanged_files: List of unchanged file paths
        - new_files: List of new file paths
        - modified_files: List of modified file paths
    """
    # Create directories
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    # Initialize state (simulating previous processing)
    now_iso = datetime.now().isoformat()
    files_dict: dict[str, dict] = {}
    state: dict = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "processed_at": now_iso,
        "files": files_dict,
    }

    # UNCHANGED FILES (2) - in state with same hash
    unchanged_files: list[Path] = []
    unchanged_content_1 = b"Unchanged document 1 content" * 20
    unchanged_file_1 = source_dir / "unchanged_1.txt"
    unchanged_file_1.write_bytes(unchanged_content_1)
    unchanged_files.append(unchanged_file_1)

    unchanged_content_2 = b"Unchanged document 2 content" * 20
    unchanged_file_2 = source_dir / "unchanged_2.txt"
    unchanged_file_2.write_bytes(unchanged_content_2)
    unchanged_files.append(unchanged_file_2)

    # Add unchanged files to state
    for file_path in unchanged_files:
        file_hash = _compute_file_hash(file_path)
        file_size = file_path.stat().st_size

        files_dict[str(file_path)] = {
            "hash": file_hash,
            "processed_at": now_iso,
            "output_path": str(output_dir / f"{file_path.stem}.json"),
            "size_bytes": file_size,
        }

    # MODIFIED FILE (1) - in state but hash differs
    modified_files: list[Path] = []
    modified_file = source_dir / "modified_1.txt"

    # First, create old content to store in state
    old_content = b"Original modified document content" * 10
    modified_file.write_bytes(old_content)
    old_hash = _compute_file_hash(modified_file)

    # Add to state with OLD hash
    files_dict[str(modified_file)] = {
        "hash": old_hash,
        "processed_at": now_iso,
        "output_path": str(output_dir / f"{modified_file.stem}.json"),
        "size_bytes": len(old_content),
    }

    # Now change the file content (simulating modification)
    new_content = b"Modified document content after update" * 15
    modified_file.write_bytes(new_content)
    modified_files.append(modified_file)

    # NEW FILES (2) - not in state
    new_files: list[Path] = []
    new_file_1 = source_dir / "new_1.pdf"
    new_file_1.write_bytes(b"%PDF-1.4\n" + b"New PDF document" * 10)
    new_files.append(new_file_1)

    new_file_2 = source_dir / "new_2.pdf"
    new_file_2.write_bytes(b"%PDF-1.4\n" + b"Another new PDF" * 10)
    new_files.append(new_file_2)

    # Write state file
    session_dir = source_dir.parent / ".data-extract-session"
    session_dir.mkdir(parents=True, exist_ok=True)
    state_file = session_dir / "incremental-state.json"
    state_file.write_text(json.dumps(state, indent=2))

    return {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "unchanged_files": unchanged_files,
        "new_files": new_files,
        "modified_files": modified_files,
    }


# ==============================================================================
# Orphan Corpus (State References Missing Files)
# ==============================================================================


@pytest.fixture
def orphan_corpus(tmp_path: Path) -> dict:
    """
    Create a corpus with orphaned output files.

    Simulates a scenario where:
    - The state file references files that no longer exist on disk
    - Output files exist but corresponding source files are missing
    - This happens when users delete source files but don't clean up state

    Useful for testing "orphan detection" and cleanup features.

    Args:
        tmp_path: Pytest built-in temporary directory

    Returns:
        Dictionary with:
        - source_dir: Path to source directory
        - output_dir: Path to output directory
        - state_file: Path to state file
        - existing_files: List of files that still exist
        - orphaned_file_paths: List of file paths in state that no longer exist
        - orphaned_output_files: List of output files with no source
    """
    # Create directories
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    now_iso = datetime.now().isoformat()
    files_dict: dict[str, dict] = {}
    state: dict = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "processed_at": now_iso,
        "files": files_dict,
    }

    # Create some actual files that still exist
    existing_files: list[Path] = []
    existing_file_1 = source_dir / "existing_1.txt"
    existing_file_1.write_text("This file still exists" * 20)
    existing_files.append(existing_file_1)

    files_dict[str(existing_file_1)] = {
        "hash": _compute_file_hash(existing_file_1),
        "processed_at": now_iso,
        "output_path": str(output_dir / "existing_1.json"),
        "size_bytes": existing_file_1.stat().st_size,
    }

    # Create output file for existing file
    (output_dir / "existing_1.json").write_text('{"status": "processed"}')

    # Add ORPHANED files to state (but don't create them on disk)
    orphaned_file_paths: list[Path] = []

    orphaned_path_1 = source_dir / "orphaned_1.pdf"
    orphaned_file_paths.append(orphaned_path_1)
    files_dict[str(orphaned_path_1)] = {
        "hash": "abc123def456" * 5,
        "processed_at": now_iso,
        "output_path": str(output_dir / "orphaned_1.json"),
        "size_bytes": 10240,
    }

    orphaned_path_2 = source_dir / "orphaned_2.pdf"
    orphaned_file_paths.append(orphaned_path_2)
    files_dict[str(orphaned_path_2)] = {
        "hash": "xyz789uvw012" * 5,
        "processed_at": now_iso,
        "output_path": str(output_dir / "orphaned_2.json"),
        "size_bytes": 20480,
    }

    # Create orphaned output files (with no corresponding source)
    orphaned_output_files: list[Path] = []
    orphaned_output_1 = output_dir / "orphaned_output_1.json"
    orphaned_output_1.write_text('{"orphaned": true}')
    orphaned_output_files.append(orphaned_output_1)

    orphaned_output_2 = output_dir / "orphaned_output_2.json"
    orphaned_output_2.write_text('{"orphaned": true}')
    orphaned_output_files.append(orphaned_output_2)

    # Write state file
    session_dir = source_dir.parent / ".data-extract-session"
    session_dir.mkdir(parents=True, exist_ok=True)
    state_file = session_dir / "incremental-state.json"
    state_file.write_text(json.dumps(state, indent=2))

    return {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "existing_files": existing_files,
        "orphaned_file_paths": orphaned_file_paths,
        "orphaned_output_files": orphaned_output_files,
    }
