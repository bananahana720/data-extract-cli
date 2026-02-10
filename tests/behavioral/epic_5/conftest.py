"""Shared fixtures for Epic 5 behavioral tests.

This module provides common fixtures for all behavioral tests in the Epic 5 test suite,
including incremental processing fixtures and corpus management.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers for Epic 5 behavioral tests."""
    config.addinivalue_line("markers", "behavioral: mark test as a behavioral validation test")
    config.addinivalue_line("markers", "story_5_7: mark test as part of Story 5-7")
    config.addinivalue_line("markers", "cli: mark test as CLI-related")
    config.addinivalue_line("markers", "incremental: mark test as incremental processing")
    config.addinivalue_line("markers", "uat: mark test as user acceptance test")


# ==============================================================================
# Incremental State Fixtures
# ==============================================================================


@pytest.fixture
def incremental_state_file(tmp_path: Path) -> Path:
    """
    Create an empty incremental state file.

    Returns:
        Path to the state file (.data-extract-session/incremental-state.json)
    """
    state_dir = tmp_path / ".data-extract-session"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "incremental-state.json"

    # Initialize with empty state
    initial_state = {
        "version": "1.0",
        "source_dir": str(tmp_path / "source"),
        "output_dir": str(tmp_path / "output"),
        "config_hash": hashlib.sha256(b"{}").hexdigest(),
        "processed_at": datetime.now().isoformat(),
        "files": {},
    }
    state_file.write_text(json.dumps(initial_state, indent=2))
    return state_file


@pytest.fixture
def processed_corpus_with_state(tmp_path: Path) -> Generator[dict, None, None]:
    """
    Create a sample corpus with files that have been previously processed.

    Provides:
    - source_dir: directory with sample documents
    - output_dir: directory with previously generated outputs
    - state_file: incremental state file tracking processed files
    - file_list: list of processed file paths

    Yields:
        dict with keys: source_dir, output_dir, state_file, file_list
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample processed files
    processed_files = {}
    for i in range(3):
        pdf_file = source_dir / f"document_{i}.pdf"
        pdf_file.write_bytes(b"PDF sample content " * 100)

        output_file = output_dir / f"document_{i}.json"
        output_file.write_text(json.dumps({"document": i, "content": "processed"}))

        # Calculate file hash
        file_hash = hashlib.sha256(pdf_file.read_bytes()).hexdigest()
        processed_files[str(pdf_file)] = {
            "hash": file_hash,
            "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "output_path": str(output_file),
            "size_bytes": pdf_file.stat().st_size,
        }

    # Create state file
    state_dir = tmp_path / ".data-extract-session"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "incremental-state.json"

    state_content = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "config_hash": hashlib.sha256(b"{}").hexdigest(),
        "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "files": processed_files,
    }
    state_file.write_text(json.dumps(state_content, indent=2))

    yield {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "file_list": list(processed_files.keys()),
    }


@pytest.fixture
def orphan_corpus(tmp_path: Path) -> Generator[dict, None, None]:
    """
    Create a corpus with orphan files (files in state but deleted from source).

    Provides:
    - source_dir: directory with only some of the original files
    - output_dir: directory with outputs for all files (including deleted ones)
    - state_file: state tracking files that no longer exist in source
    - deleted_files: list of files that were deleted from source

    Yields:
        dict with keys: source_dir, output_dir, state_file, deleted_files
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create state for files that will be partially deleted
    processed_files = {}
    deleted_files = []

    # Files that remain in source
    for i in range(2):
        pdf_file = source_dir / f"document_{i}.pdf"
        pdf_file.write_bytes(b"PDF sample content " * 100)
        file_hash = hashlib.sha256(pdf_file.read_bytes()).hexdigest()
        processed_files[str(pdf_file)] = {
            "hash": file_hash,
            "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "output_path": str(output_dir / f"document_{i}.json"),
            "size_bytes": pdf_file.stat().st_size,
        }

    # Files that don't exist in source anymore (orphans)
    for i in range(2, 5):
        orphan_path = str(source_dir / f"document_{i}.pdf")
        deleted_files.append(orphan_path)
        processed_files[orphan_path] = {
            "hash": hashlib.sha256(f"deleted_{i}".encode()).hexdigest(),
            "processed_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "output_path": str(output_dir / f"document_{i}.json"),
            "size_bytes": 1024,
        }

    # Create state file
    state_dir = tmp_path / ".data-extract-session"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "incremental-state.json"

    state_content = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "config_hash": hashlib.sha256(b"{}").hexdigest(),
        "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "files": processed_files,
    }
    state_file.write_text(json.dumps(state_content, indent=2))

    yield {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "deleted_files": deleted_files,
    }


@pytest.fixture
def mixed_corpus(tmp_path: Path) -> Generator[dict, None, None]:
    """
    Create a corpus with a mix of unchanged, modified, and new files.

    Provides:
    - source_dir: directory with all three types of files
    - output_dir: directory with outputs
    - state_file: state tracking previous processing
    - unchanged_files: files with same hash as in state
    - modified_files: files with different content than in state
    - new_files: files not in state

    Yields:
        dict with all the above plus counts
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    unchanged_files = []
    modified_files = []
    new_files = []
    processed_files = {}

    # Unchanged files - same content
    unchanged_content = b"PDF unchanged content " * 50
    for i in range(2):
        pdf_file = source_dir / f"unchanged_{i}.pdf"
        pdf_file.write_bytes(unchanged_content)
        file_hash = hashlib.sha256(unchanged_content).hexdigest()
        processed_files[str(pdf_file)] = {
            "hash": file_hash,
            "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "output_path": str(output_dir / f"unchanged_{i}.json"),
            "size_bytes": len(unchanged_content),
        }
        unchanged_files.append(str(pdf_file))

    # Modified files - different content
    for i in range(2):
        pdf_file = source_dir / f"modified_{i}.pdf"
        pdf_file.write_bytes(b"PDF modified content new " * 50)
        # Store old hash in state
        processed_files[str(pdf_file)] = {
            "hash": hashlib.sha256(b"PDF modified content old " * 50).hexdigest(),
            "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "output_path": str(output_dir / f"modified_{i}.json"),
            "size_bytes": 1024,
        }
        modified_files.append(str(pdf_file))

    # New files - not in state
    for i in range(2):
        pdf_file = source_dir / f"new_{i}.pdf"
        pdf_file.write_bytes(b"PDF new content " * 60)
        new_files.append(str(pdf_file))

    # Create state file (only for unchanged and modified)
    state_dir = tmp_path / ".data-extract-session"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "incremental-state.json"

    state_content = {
        "version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "config_hash": hashlib.sha256(b"{}").hexdigest(),
        "processed_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "files": processed_files,
    }
    state_file.write_text(json.dumps(state_content, indent=2))

    yield {
        "source_dir": source_dir,
        "output_dir": output_dir,
        "state_file": state_file,
        "unchanged_files": unchanged_files,
        "modified_files": modified_files,
        "new_files": new_files,
        "unchanged_count": len(unchanged_files),
        "modified_count": len(modified_files),
        "new_count": len(new_files),
    }
