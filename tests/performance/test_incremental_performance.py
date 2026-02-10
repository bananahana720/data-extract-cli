"""Performance Tests for Incremental Processing (Story 5-7).

Validates performance requirements:
- State check startup: <2 seconds for 1000+ files
- Hash calculation: reasonable speed for large files
- State file load: <100ms for 1000+ entries

Story 5-7: Batch Processing Optimization and Incremental Updates
Reference: docs/stories/5-7-batch-processing-optimization.md
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
    pytest.mark.story_5_7,
]


class TestIncrementalPerformance:
    """Performance tests for incremental processing components."""

    def test_state_check_startup_under_2_seconds(self, tmp_path: Path) -> None:
        """
        RED: Verify incremental state check completes in <2 seconds.

        Tests the startup performance when:
        - State file contains 1000+ previously processed files
        - Scanning source directory with same files
        - No actual processing, just change detection

        Requirement: <2 seconds startup overhead

        Expected RED failure: Performance not optimized
        """

        # Given
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create state with 1000+ files
        processed_files = {}
        for i in range(1001):
            filename = f"document_{i:04d}.pdf"
            pdf_file = source_dir / filename
            pdf_file.write_bytes(b"PDF sample content " * 10)
            file_hash = hashlib.sha256(pdf_file.read_bytes()).hexdigest()
            processed_files[str(pdf_file)] = {
                "hash": file_hash,
                "processed_at": "2025-01-01T00:00:00",
                "output_path": str(tmp_path / "output" / f"{filename}.json"),
                "size_bytes": pdf_file.stat().st_size,
            }

        # Create state file
        state_dir = tmp_path / ".data-extract-session"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "incremental-state.json"

        state_content = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "output_dir": str(tmp_path / "output"),
            "config_hash": hashlib.sha256(b"{}").hexdigest(),
            "processed_at": "2025-01-01T00:00:00",
            "files": processed_files,
        }
        state_file.write_text(json.dumps(state_content, indent=2))

        # When
        from data_extract.cli.batch import IncrementalProcessor

        start_time = time.perf_counter()
        processor = IncrementalProcessor(source_dir, tmp_path / "output")
        change_summary = processor.analyze()
        elapsed = time.perf_counter() - start_time

        # Then
        assert elapsed < 2.0, f"State check took {elapsed:.2f}s, " f"requirement is <2.0s"
        assert change_summary.unchanged_count == 1001

    def test_hash_calculation_reasonable_for_large_files(self, tmp_path: Path) -> None:
        """
        RED: Verify hash calculation is efficient for large files.

        Tests hashing performance:
        - File size: ~100MB (large PDF)
        - Requirement: <5 seconds per file
        - Should use streaming, not load entire file into memory

        Expected RED failure: Using inefficient hashing method
        """

        # Given
        large_file = tmp_path / "large.bin"
        # Create 100MB file in chunks (don't load all into memory)
        target_size = 100 * 1024 * 1024  # 100MB
        chunk_size = 1024 * 1024  # 1MB chunks
        bytes_written = 0

        with open(large_file, "wb") as f:
            while bytes_written < target_size:
                chunk = b"x" * min(chunk_size, target_size - bytes_written)
                f.write(chunk)
                bytes_written += len(chunk)

        # When
        from data_extract.cli.batch import FileHasher

        start_time = time.perf_counter()
        file_hash = FileHasher.compute_hash(large_file)
        elapsed = time.perf_counter() - start_time

        # Then
        assert elapsed < 5.0, f"Hashing 100MB file took {elapsed:.2f}s, " f"requirement is <5.0s"
        assert len(file_hash) == 64  # SHA256 is 64 hex chars

    def test_state_file_load_under_100ms(self, tmp_path: Path) -> None:
        """
        RED: Verify state file loading is fast (<100ms).

        Tests state file loading performance:
        - State file with 1000+ entries
        - JSON parsing and validation
        - Requirement: <100ms load time

        Expected RED failure: Loading not optimized
        """

        # Given
        state_file = tmp_path / "state.json"

        # Create large state file
        processed_files = {}
        for i in range(1000):
            processed_files[f"/path/to/document_{i:04d}.pdf"] = {
                "hash": hashlib.sha256(f"content_{i}".encode()).hexdigest(),
                "processed_at": "2025-01-01T00:00:00",
                "output_path": f"/output/document_{i:04d}.json",
                "size_bytes": 10240 + i * 100,
            }

        state_content = {
            "version": "1.0",
            "source_dir": "/path/to/source",
            "output_dir": "/path/to/output",
            "config_hash": hashlib.sha256(b"{}").hexdigest(),
            "processed_at": "2025-01-01T00:00:00",
            "files": processed_files,
        }
        state_file.write_text(json.dumps(state_content, indent=2))

        # When
        from data_extract.cli.batch import StateFile

        # Save the state first to the correct location
        session_dir = tmp_path / ".data-extract-session"
        session_dir.mkdir(parents=True, exist_ok=True)
        actual_state_file = session_dir / "incremental-state.json"
        actual_state_file.write_text(state_file.read_text())

        state_manager = StateFile(tmp_path)
        start_time = time.perf_counter()
        loaded_state = state_manager.load()
        elapsed = time.perf_counter() - start_time

        # Then
        assert elapsed < 0.1, (
            f"Loading state file took {elapsed*1000:.2f}ms, " f"requirement is <100ms"
        )
        assert loaded_state is not None
        assert len(loaded_state["files"]) == 1000
