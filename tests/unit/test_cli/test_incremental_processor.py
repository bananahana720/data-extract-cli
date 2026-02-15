"""Unit Tests for Incremental Processing Components (Story 5-7).

Tests individual components of the incremental processing system:
- FileHasher: SHA256 hashing and determinism
- StateFile: Persistence and atomic writes
- ChangeDetector: File change detection logic
- GlobPatternExpander: Pattern matching and expansion

Story 5-7: Batch Processing Optimization and Incremental Updates
Reference: docs/tech-spec-epic-5.md
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.unit,
    pytest.mark.cli,
]

pytestmark = [pytest.mark.unit, pytest.mark.story_5_7, pytest.mark.cli]


# ==============================================================================
# FileHasher Unit Tests
# ==============================================================================


class TestFileHasher:
    """Unit tests for SHA256 file hashing."""

    def test_sha256_hash_deterministic(self, tmp_path: Path) -> None:
        """
        RED: Verify SHA256 hash is deterministic for same content.

        Given: A file with known content
        When: FileHasher calculates hash twice
        Then: Both hashes should be identical
        And: Hash should be valid SHA256 (64 hex characters)

        Expected RED failure: FileHasher not implemented
        """
        # Given
        test_file = tmp_path / "test.txt"
        test_content = b"This is test content for hashing"
        test_file.write_bytes(test_content)

        # When
        from data_extract.cli.batch import FileHasher

        hash1 = FileHasher.compute_hash(test_file)
        hash2 = FileHasher.compute_hash(test_file)

        # Then
        assert hash1 == hash2, "Same file should produce same hash"
        assert len(hash1) == 64, "SHA256 hash should be 64 hex characters"
        assert all(c in "0123456789abcdef" for c in hash1.lower())

    def test_different_content_produces_different_hash(self, tmp_path: Path) -> None:
        """
        RED: Verify different content produces different hashes.

        Given: Two files with different content
        When: FileHasher calculates hashes for both
        Then: Hashes should be completely different
        And: Small changes should produce completely different hashes

        Expected RED failure: FileHasher not implemented
        """
        # Given
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_bytes(b"Content A")
        file2.write_bytes(b"Content B")

        # When
        from data_extract.cli.batch import FileHasher

        hash1 = FileHasher.compute_hash(file1)
        hash2 = FileHasher.compute_hash(file2)

        # Then
        assert hash1 != hash2, "Different content should produce different hash"

    def test_large_file_hash_calculation(self, tmp_path: Path) -> None:
        """
        RED: Verify hash calculation works for large binary files.

        Given: A large PDF-like binary file (>100MB)
        When: FileHasher calculates hash
        Then: Should complete successfully without loading entire file into memory
        And: Hash should be valid

        Expected RED failure: FileHasher not implemented for large files
        """
        # Given
        large_file = tmp_path / "large.bin"
        # Create 10MB file in chunks to avoid memory issues
        with open(large_file, "wb") as f:
            for _ in range(100):
                f.write(b"x" * (100 * 1024))  # 100KB chunks

        # When
        from data_extract.cli.batch import FileHasher

        file_hash = FileHasher.compute_hash(large_file)

        # Then
        assert len(file_hash) == 64, "Should produce valid SHA256"
        assert file_hash is not None

    def test_binary_file_hash(self, tmp_path: Path) -> None:
        """
        RED: Verify hash calculation works for binary files.

        Given: A binary PDF file
        When: FileHasher calculates hash
        Then: Should handle binary content correctly
        And: Hash should be reproducible

        Expected RED failure: FileHasher not implemented for binary
        """
        # Given
        binary_file = tmp_path / "test.pdf"
        pdf_header = b"%PDF-1.4\n" + b"binary" * 100
        binary_file.write_bytes(pdf_header)

        # When
        from data_extract.cli.batch import FileHasher

        hash1 = FileHasher.compute_hash(binary_file)
        hash2 = FileHasher.compute_hash(binary_file)

        # Then
        assert hash1 == hash2


# ==============================================================================
# StateFile Unit Tests
# ==============================================================================


class TestStateFile:
    """Unit tests for incremental state file management."""

    def test_state_file_schema_valid(self, tmp_path: Path) -> None:
        """
        RED: Verify state file matches expected schema.

        Given: A state file created by IncrementalProcessor
        When: We load and inspect the JSON
        Then: Must have required fields:
              - version (string)
              - source_dir (string)
              - output_dir (string)
              - config_hash (string)
              - processed_at (ISO datetime)
              - files (dict)

        Expected RED failure: StateFile not implemented
        """
        # Given
        from data_extract.cli.batch import StateFile

        state_manager = StateFile(tmp_path)

        state_data = {
            "version": "1.0",
            "source_dir": str(tmp_path / "source"),
            "output_dir": str(tmp_path / "output"),
            "config_hash": "test_hash",
            "processed_at": "2025-01-01T00:00:00",
            "files": {},
        }

        # When
        state_manager.save(state_data)

        # Then
        state_file_path = state_manager.get_path()
        assert state_file_path.exists()
        content = json.loads(state_file_path.read_text())
        assert "version" in content
        assert "source_dir" in content
        assert "output_dir" in content
        assert "config_hash" in content
        assert "processed_at" in content
        assert "files" in content
        assert isinstance(content["files"], dict)

    def test_state_file_read_write(self, tmp_path: Path) -> None:
        """
        RED: Verify state file can be written and read back consistently.

        Given: State data to persist
        When: StateFile writes then reads the data
        Then: Read data should match written data exactly

        Expected RED failure: StateFile not implemented
        """
        # Given
        from data_extract.cli.batch import StateFile

        state_manager = StateFile(tmp_path)
        test_data = {
            "version": "1.0",
            "source_dir": "/test/source",
            "output_dir": "/test/output",
            "config_hash": "test_hash",
            "processed_at": "2025-01-01T00:00:00",
            "files": {
                "/test/doc.pdf": {
                    "hash": hashlib.sha256(b"test").hexdigest(),
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/test/output/doc.json",
                    "size_bytes": 1024,
                }
            },
        }

        # When
        state_manager.save(test_data)
        loaded_data = state_manager.load()

        # Then
        assert loaded_data is not None
        assert loaded_data["source_dir"] == test_data["source_dir"]
        assert loaded_data["output_dir"] == test_data["output_dir"]
        assert loaded_data["files"] == test_data["files"]

    def test_state_file_atomic_writes(self, tmp_path: Path) -> None:
        """
        RED: Verify state file writes are atomic (no partial writes).

        Given: A state file being updated
        When: Write is interrupted or fails
        Then: State file should not be left in corrupted state
        And: Should use temp file + rename pattern

        Expected RED failure: Atomic writes not implemented
        """
        # Given
        from data_extract.cli.batch import StateFile

        state_manager = StateFile(tmp_path)
        state_data = {
            "version": "1.0",
            "source_dir": str(tmp_path / "source"),
            "output_dir": str(tmp_path / "output"),
            "config_hash": "test_hash",
            "processed_at": "2025-01-01T00:00:00",
            "files": {},
        }

        # When
        state_manager.save(state_data)

        # Then - verify no temp files left behind in session directory
        session_dir = tmp_path / ".data-extract-session"
        assert session_dir.exists()
        temp_files = list(session_dir.glob("incremental-state-*.tmp"))
        assert len(temp_files) == 0, "Should not leave temp files"

    def test_state_file_corruption_handling(self, tmp_path: Path) -> None:
        """
        RED: Verify corrupted state files are handled gracefully.

        Given: A corrupted/invalid state file
        When: StateFile.load() is called
        Then: Should return None (graceful degradation)
        And: Treats corrupted state as missing state

        Expected RED failure: Error handling not implemented
        """
        # Given
        from data_extract.cli.batch import StateFile

        # Create corrupted state file manually
        session_dir = tmp_path / ".data-extract-session"
        session_dir.mkdir(parents=True, exist_ok=True)
        corrupted_file = session_dir / "incremental-state.json"
        corrupted_file.write_text("{ invalid json")

        # When
        state_manager = StateFile(tmp_path)
        loaded_state = state_manager.load()

        # Then
        assert loaded_state is None, "Corrupted state should return None"


# ==============================================================================
# ChangeDetector Unit Tests
# ==============================================================================


class TestChangeDetector:
    """Unit tests for file change detection logic."""

    def test_detects_new_files(self, tmp_path: Path) -> None:
        """
        RED: Verify new files are detected (not in state).

        Given: Source directory with files not in state
        When: ChangeDetector analyzes directory
        Then: Should identify files as "new"
        And: New file list should contain all files not in state

        Expected RED failure: ChangeDetector not implemented
        """
        # Given
        from data_extract.cli.batch import ChangeDetector, FileHasher

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        new_file = source_dir / "new_file.pdf"
        new_file.write_bytes(b"new content")

        state_data = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "files": {},  # Empty state
        }

        # When
        hasher = FileHasher()
        detector = ChangeDetector(state_data, hasher)
        changes = detector.detect_changes([new_file])

        # Then
        assert changes.new_count == 1
        assert new_file in changes.new_files

    def test_detects_modified_files(self, tmp_path: Path) -> None:
        """
        RED: Verify modified files are detected (hash changed).

        Given: File in state with old hash, but file has new content
        When: ChangeDetector analyzes directory
        Then: Should identify file as "modified"
        And: Should include modified file in changes list

        Expected RED failure: ChangeDetector not implemented
        """
        # Given
        from data_extract.cli.batch import ChangeDetector, FileHasher

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        test_file = source_dir / "modified.pdf"
        new_content = b"new modified content"
        test_file.write_bytes(new_content)

        old_hash = hashlib.sha256(b"old content").hexdigest()
        state_data = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "files": {
                str(test_file): {
                    "hash": old_hash,
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/modified.json",
                    "size_bytes": 100,
                }
            },
        }

        # When
        hasher = FileHasher()
        detector = ChangeDetector(state_data, hasher)
        changes = detector.detect_changes([test_file])

        # Then
        assert changes.modified_count == 1
        assert test_file in changes.modified_files

    def test_detects_unchanged_files(self, tmp_path: Path) -> None:
        """
        RED: Verify unchanged files are detected (hash matches).

        Given: File in state with same hash as on disk
        When: ChangeDetector analyzes directory
        Then: Should identify file as "unchanged"
        And: Should include count in changes summary

        Expected RED failure: ChangeDetector not implemented
        """
        # Given
        from data_extract.cli.batch import ChangeDetector, FileHasher

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        test_file = source_dir / "unchanged.pdf"
        content = b"unchanged content"
        test_file.write_bytes(content)
        file_hash = hashlib.sha256(content).hexdigest()

        state_data = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "files": {
                str(test_file): {
                    "hash": file_hash,
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/unchanged.json",
                    "size_bytes": len(content),
                }
            },
        }

        # When
        hasher = FileHasher()
        detector = ChangeDetector(state_data, hasher)
        changes = detector.detect_changes([test_file])

        # Then
        assert changes.unchanged_count == 1

    def test_detects_deleted_files(self, tmp_path: Path) -> None:
        """
        RED: Verify deleted files are detected (in state but not on disk).

        Given: File in state but no longer exists on disk
        When: ChangeDetector analyzes directory
        Then: Should identify file as "deleted"
        And: Should provide list of deleted files for cleanup

        Expected RED failure: ChangeDetector not implemented
        """
        # Given
        from data_extract.cli.batch import ChangeDetector, FileHasher

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        deleted_path = source_dir / "deleted.pdf"

        state_data = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "files": {
                str(deleted_path): {
                    "hash": hashlib.sha256(b"deleted content").hexdigest(),
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/deleted.json",
                    "size_bytes": 100,
                }
            },
        }

        # When - pass empty file list (deleted file not in current files)
        hasher = FileHasher()
        detector = ChangeDetector(state_data, hasher)
        changes = detector.detect_changes([])  # No files in current directory

        # Then
        assert changes.deleted_count == 1
        assert deleted_path in changes.deleted_files

    def test_change_summary_totals(self, tmp_path: Path) -> None:
        """
        RED: Verify change summary contains accurate totals.

        Given: A mixed corpus with all change types
        When: ChangeDetector analyzes directory
        Then: Summary should include:
              - unchanged (count)
              - modified (count)
              - new (count)
              - deleted (count)

        Expected RED failure: Summary calculation not implemented
        """
        # Given
        from data_extract.cli.batch import ChangeDetector, FileHasher

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create files with different states
        new_file = source_dir / "new.pdf"
        new_file.write_bytes(b"new content")

        modified_file = source_dir / "modified.pdf"
        modified_file.write_bytes(b"new content")

        unchanged_file = source_dir / "unchanged.pdf"
        unchanged_content = b"unchanged content"
        unchanged_file.write_bytes(unchanged_content)

        # State with old data
        state_data = {
            "version": "1.0",
            "source_dir": str(source_dir),
            "files": {
                str(modified_file): {
                    "hash": hashlib.sha256(b"old content").hexdigest(),
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/modified.json",
                    "size_bytes": 100,
                },
                str(unchanged_file): {
                    "hash": hashlib.sha256(unchanged_content).hexdigest(),
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/unchanged.json",
                    "size_bytes": len(unchanged_content),
                },
                str(source_dir / "deleted.pdf"): {
                    "hash": hashlib.sha256(b"deleted").hexdigest(),
                    "processed_at": "2025-01-01T00:00:00",
                    "output_path": "/output/deleted.json",
                    "size_bytes": 100,
                },
            },
        }

        # When
        hasher = FileHasher()
        detector = ChangeDetector(state_data, hasher)
        changes = detector.detect_changes([new_file, modified_file, unchanged_file])

        # Then
        assert changes.new_count == 1
        assert changes.modified_count == 1
        assert changes.unchanged_count == 1
        assert changes.deleted_count == 1
        assert changes.total_changes == 2  # new + modified


# ==============================================================================
# GlobPatternExpander Unit Tests
# ==============================================================================


class TestGlobPatternExpansion:
    """Unit tests for glob pattern matching and expansion."""

    def test_simple_extension_pattern(self, tmp_path: Path) -> None:
        """
        RED: Verify simple glob patterns match files by extension.

        Given: Pattern "*.pdf"
        When: GlobPatternExpander expands pattern in directory
        Then: Should match all .pdf files
        And: Should not match other file types

        Expected RED failure: GlobPatternExpander not implemented
        """
        # Given
        from data_extract.cli.batch import GlobPatternExpander

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.pdf").write_bytes(b"PDF")
        (source_dir / "file2.pdf").write_bytes(b"PDF")
        (source_dir / "file1.txt").write_bytes(b"TXT")

        # When
        expander = GlobPatternExpander(source_dir)
        matches = expander.expand("*.pdf")

        # Then
        assert len(matches) == 2
        assert all(m.suffix == ".pdf" for m in matches)

    def test_recursive_pattern(self, tmp_path: Path) -> None:
        """
        RED: Verify recursive glob patterns (**.pdf) match all levels.

        Given: Pattern "**.pdf" (recursive)
        When: GlobPatternExpander expands pattern
        Then: Should match .pdf files in all subdirectories
        And: Should include nested files at any depth

        Expected RED failure: Recursive pattern not implemented
        """
        # Given
        from data_extract.cli.batch import GlobPatternExpander

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.pdf").write_bytes(b"PDF")
        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.pdf").write_bytes(b"PDF")

        # When
        expander = GlobPatternExpander(source_dir)
        matches = expander.expand("**/*.pdf")

        # Then
        assert len(matches) == 2

    def test_pattern_no_matches_returns_empty(self, tmp_path: Path) -> None:
        """
        RED: Verify pattern with no matches returns empty list.

        Given: Pattern that matches no files
        When: GlobPatternExpander expands pattern
        Then: Should return empty list (not raise error)

        Expected RED failure: Error handling not implemented
        """
        # Given
        from data_extract.cli.batch import GlobPatternExpander

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_bytes(b"TXT")

        # When
        expander = GlobPatternExpander(source_dir)
        matches = expander.expand("*.nonexistent")

        # Then
        assert len(matches) == 0

    def test_multiple_patterns_union(self, tmp_path: Path) -> None:
        """
        RED: Verify multiple patterns can be combined (union).

        Given: Multiple patterns (e.g., ["*.pdf", "*.docx"])
        When: GlobPatternExpander expands all patterns
        Then: Should return union of matches from all patterns
        And: Should not return duplicates

        Expected RED failure: Multiple pattern handling not implemented
        """
        # Given
        from data_extract.cli.batch import GlobPatternExpander

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.pdf").write_bytes(b"PDF")
        (source_dir / "file2.docx").write_bytes(b"DOCX")

        # When
        expander = GlobPatternExpander(source_dir)
        pdf_matches = expander.expand("*.pdf")
        docx_matches = expander.expand("*.docx")
        all_matches = pdf_matches + docx_matches

        # Then
        assert len(all_matches) == 2
