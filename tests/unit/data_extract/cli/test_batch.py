"""Unit tests for batch processing and incremental updates module.

Tests coverage:
- FileHasher: SHA256 computation with chunked reading
- StateFile: Load/save operations with atomic writes
- ChangeDetector: File change detection (new/modified/unchanged/deleted)
- GlobPatternExpander: Pattern expansion with recursive support
- IncrementalProcessor: Orchestration and status reporting
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from data_extract.cli.batch import (
    ChangeDetector,
    ChangeSummary,
    FileHasher,
    GlobPatternExpander,
    IncrementalProcessor,
    ProcessingResult,
    StateFile,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


# ============================================================================
# FileHasher Tests
# ============================================================================


class TestFileHasher:
    """Tests for FileHasher utility."""

    def test_compute_hash_simple_file(self, tmp_path: Path) -> None:
        """Test hash computation for a simple file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        # Compute hash
        hash_value = FileHasher.compute_hash(test_file)

        # Verify hash is a hex string
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_consistency(self, tmp_path: Path) -> None:
        """Test that same content produces same hash."""
        # Create two files with identical content
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = b"identical content"

        file1.write_bytes(content)
        file2.write_bytes(content)

        # Hashes should match
        hash1 = FileHasher.compute_hash(file1)
        hash2 = FileHasher.compute_hash(file2)
        assert hash1 == hash2

    def test_compute_hash_different_content(self, tmp_path: Path) -> None:
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_bytes(b"content A")
        file2.write_bytes(b"content B")

        hash1 = FileHasher.compute_hash(file1)
        hash2 = FileHasher.compute_hash(file2)
        assert hash1 != hash2

    def test_compute_hash_large_file(self, tmp_path: Path) -> None:
        """Test hash computation with chunked reading for large files."""
        # Create file larger than chunk size (8192 bytes)
        large_file = tmp_path / "large.bin"
        content = b"A" * 20000  # 20KB
        large_file.write_bytes(content)

        # Should compute hash without issues
        hash_value = FileHasher.compute_hash(large_file)
        assert len(hash_value) == 64

    def test_compute_hash_empty_file(self, tmp_path: Path) -> None:
        """Test hash computation for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")

        hash_value = FileHasher.compute_hash(empty_file)
        assert len(hash_value) == 64
        # SHA256 of empty string
        assert hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_compute_hash_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for missing files."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError, match="File not found"):
            FileHasher.compute_hash(nonexistent)

    def test_compute_hash_permission_error(self, tmp_path: Path) -> None:
        """Test that PermissionError is handled properly."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError, match="Permission denied reading file"):
                FileHasher.compute_hash(test_file)


# ============================================================================
# StateFile Tests
# ============================================================================


class TestStateFile:
    """Tests for StateFile persistence."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test state file initialization."""
        state_file = StateFile(tmp_path)

        assert state_file.work_dir == tmp_path
        assert state_file.session_dir == tmp_path / ".data-extract-session"
        assert (
            state_file.state_path == tmp_path / ".data-extract-session" / "incremental-state.json"
        )

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading when state file doesn't exist."""
        state_file = StateFile(tmp_path)
        result = state_file.load()

        assert result is None

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading state."""
        state_file = StateFile(tmp_path)

        # Test data
        state_data = {
            "version": "1.0",
            "source_dir": "/path/to/source",
            "files": {"file1.pdf": {"hash": "abc123"}},
        }

        # Save state
        state_file.save(state_data)

        # Verify file exists
        assert state_file.exists()

        # Load state
        loaded = state_file.load()
        assert loaded == state_data

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test that save creates session directory if needed."""
        state_file = StateFile(tmp_path)

        # Session directory should not exist initially
        assert not state_file.session_dir.exists()

        # Save should create directory
        state_file.save({"version": "1.0"})
        assert state_file.session_dir.exists()

    def test_save_atomic_write(self, tmp_path: Path) -> None:
        """Test atomic write pattern (uses temp file)."""
        state_file = StateFile(tmp_path)

        state_data = {"version": "1.0", "data": "test"}
        state_file.save(state_data)

        # Verify no temp files remain
        temp_files = list(state_file.session_dir.glob("incremental-state-*.tmp"))
        assert len(temp_files) == 0

        # Verify final file exists
        assert state_file.state_path.exists()

    def test_load_corrupted_json(self, tmp_path: Path) -> None:
        """Test loading corrupted JSON returns None."""
        state_file = StateFile(tmp_path)

        # Create corrupted JSON file
        state_file.session_dir.mkdir(parents=True, exist_ok=True)
        state_file.state_path.write_text("{ invalid json }")

        # Should return None for corrupted data
        result = state_file.load()
        assert result is None

    def test_exists_method(self, tmp_path: Path) -> None:
        """Test exists() method."""
        state_file = StateFile(tmp_path)

        assert not state_file.exists()

        state_file.save({"version": "1.0"})

        assert state_file.exists()

    def test_get_path_method(self, tmp_path: Path) -> None:
        """Test get_path() returns correct path."""
        state_file = StateFile(tmp_path)

        path = state_file.get_path()
        assert path == tmp_path / ".data-extract-session" / "incremental-state.json"


# ============================================================================
# ChangeDetector Tests
# ============================================================================


class TestChangeDetector:
    """Tests for ChangeDetector."""

    def test_detect_new_files(self, tmp_path: Path) -> None:
        """Test detection of new files (not in state)."""
        # Create test files
        file1 = tmp_path / "new1.pdf"
        file2 = tmp_path / "new2.pdf"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")

        # Empty state
        detector = ChangeDetector(state=None, hasher=FileHasher())

        # Detect changes
        changes = detector.detect_changes([file1, file2])

        assert changes.new_count == 2
        assert changes.modified_count == 0
        assert changes.unchanged_count == 0
        assert changes.deleted_count == 0
        assert file1 in changes.new_files
        assert file2 in changes.new_files

    def test_detect_modified_files(self, tmp_path: Path) -> None:
        """Test detection of modified files (hash changed)."""
        # Create file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"original content")

        # Create state with old hash
        original_hash = FileHasher.compute_hash(test_file)

        # Modify file
        test_file.write_bytes(b"modified content")

        state = {
            "files": {
                str(test_file): {
                    "hash": original_hash,  # Old hash
                    "processed_at": "2025-11-30T10:00:00Z",
                }
            }
        }

        detector = ChangeDetector(state=state, hasher=FileHasher())
        changes = detector.detect_changes([test_file])

        assert changes.new_count == 0
        assert changes.modified_count == 1
        assert changes.unchanged_count == 0
        assert test_file in changes.modified_files

    def test_detect_unchanged_files(self, tmp_path: Path) -> None:
        """Test detection of unchanged files (hash matches)."""
        # Create file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"content")

        # Create state with current hash
        current_hash = FileHasher.compute_hash(test_file)

        state = {
            "files": {
                str(test_file): {
                    "hash": current_hash,
                    "processed_at": "2025-11-30T10:00:00Z",
                }
            }
        }

        detector = ChangeDetector(state=state, hasher=FileHasher())
        changes = detector.detect_changes([test_file])

        assert changes.new_count == 0
        assert changes.modified_count == 0
        assert changes.unchanged_count == 1
        assert test_file in changes.unchanged_files

    def test_detect_deleted_files(self, tmp_path: Path) -> None:
        """Test detection of deleted files (in state but not in current files)."""
        deleted_path = tmp_path / "deleted.pdf"

        # State has file that no longer exists
        state = {
            "files": {
                str(deleted_path): {
                    "hash": "abc123",
                    "processed_at": "2025-11-30T10:00:00Z",
                }
            }
        }

        detector = ChangeDetector(state=state, hasher=FileHasher())

        # Check with empty file list
        changes = detector.detect_changes([])

        assert changes.new_count == 0
        assert changes.modified_count == 0
        assert changes.unchanged_count == 0
        assert changes.deleted_count == 1
        assert deleted_path in changes.deleted_files

    def test_detect_mixed_changes(self, tmp_path: Path) -> None:
        """Test detection with multiple change types."""
        # New file
        new_file = tmp_path / "new.pdf"
        new_file.write_bytes(b"new")

        # Modified file
        modified_file = tmp_path / "modified.pdf"
        modified_file.write_bytes(b"original")
        original_hash = FileHasher.compute_hash(modified_file)
        modified_file.write_bytes(b"changed")

        # Unchanged file
        unchanged_file = tmp_path / "unchanged.pdf"
        unchanged_file.write_bytes(b"same")
        unchanged_hash = FileHasher.compute_hash(unchanged_file)

        # Deleted file
        deleted_path = tmp_path / "deleted.pdf"

        state = {
            "files": {
                str(modified_file): {"hash": original_hash},
                str(unchanged_file): {"hash": unchanged_hash},
                str(deleted_path): {"hash": "old_hash"},
            }
        }

        detector = ChangeDetector(state=state, hasher=FileHasher())
        changes = detector.detect_changes([new_file, modified_file, unchanged_file])

        assert changes.new_count == 1
        assert changes.modified_count == 1
        assert changes.unchanged_count == 1
        assert changes.deleted_count == 1

    def test_file_access_error_treated_as_modified(self, tmp_path: Path) -> None:
        """Test that inaccessible files are treated as modified to retry."""
        test_file = tmp_path / "test.pdf"

        state = {
            "files": {
                str(test_file): {
                    "hash": "abc123",
                    "processed_at": "2025-11-30T10:00:00Z",
                }
            }
        }

        detector = ChangeDetector(state=state, hasher=FileHasher())

        # File doesn't exist, should trigger FileNotFoundError in hash computation
        changes = detector.detect_changes([test_file])

        # Should be treated as modified to retry
        assert changes.modified_count == 1
        assert test_file in changes.modified_files


# ============================================================================
# ChangeSummary Tests
# ============================================================================


class TestChangeSummary:
    """Tests for ChangeSummary dataclass properties."""

    def test_count_properties(self) -> None:
        """Test count properties calculate correctly."""
        summary = ChangeSummary(
            new_files=[Path("a"), Path("b")],
            modified_files=[Path("c")],
            unchanged_files=[Path("d"), Path("e"), Path("f")],
            deleted_files=[Path("g")],
        )

        assert summary.new_count == 2
        assert summary.modified_count == 1
        assert summary.unchanged_count == 3
        assert summary.deleted_count == 1

    def test_total_changes(self) -> None:
        """Test total_changes property (new + modified)."""
        summary = ChangeSummary(
            new_files=[Path("a"), Path("b")],
            modified_files=[Path("c"), Path("d")],
            unchanged_files=[Path("e")],
            deleted_files=[],
        )

        assert summary.total_changes == 4  # 2 new + 2 modified

    def test_empty_summary(self) -> None:
        """Test empty summary has zero counts."""
        summary = ChangeSummary(
            new_files=[],
            modified_files=[],
            unchanged_files=[],
            deleted_files=[],
        )

        assert summary.new_count == 0
        assert summary.modified_count == 0
        assert summary.unchanged_count == 0
        assert summary.deleted_count == 0
        assert summary.total_changes == 0


# ============================================================================
# GlobPatternExpander Tests
# ============================================================================


class TestGlobPatternExpander:
    """Tests for GlobPatternExpander."""

    def test_simple_pattern(self, tmp_path: Path) -> None:
        """Test simple glob pattern (*.pdf)."""
        # Create test files
        (tmp_path / "doc1.pdf").write_bytes(b"test")
        (tmp_path / "doc2.pdf").write_bytes(b"test")
        (tmp_path / "doc3.docx").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)
        matches = expander.expand("*.pdf")

        assert len(matches) == 2
        assert all(f.suffix == ".pdf" for f in matches)

    def test_recursive_pattern(self, tmp_path: Path) -> None:
        """Test recursive pattern (**/*.pdf)."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.pdf").write_bytes(b"test")
        (subdir / "nested.pdf").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)
        matches = expander.expand("**/*.pdf")

        assert len(matches) == 2
        assert any(f.name == "root.pdf" for f in matches)
        assert any(f.name == "nested.pdf" for f in matches)

    def test_multiple_extensions(self, tmp_path: Path) -> None:
        """Test pattern with multiple extensions (*.{pdf,docx})."""
        (tmp_path / "doc.pdf").write_bytes(b"test")
        (tmp_path / "doc.docx").write_bytes(b"test")
        (tmp_path / "sheet.xlsx").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)

        # Test PDF pattern
        pdf_matches = expander.expand("*.pdf")
        assert len(pdf_matches) == 1

        # Test DOCX pattern
        docx_matches = expander.expand("*.docx")
        assert len(docx_matches) == 1

    def test_no_matches(self, tmp_path: Path) -> None:
        """Test pattern with no matches returns empty list."""
        (tmp_path / "doc.txt").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)
        matches = expander.expand("*.pdf")

        assert len(matches) == 0

    def test_excludes_directories(self, tmp_path: Path) -> None:
        """Test that directories are excluded from results."""
        # Create directory and file with same pattern
        (tmp_path / "test.pdf").mkdir()
        (tmp_path / "doc.pdf").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)
        matches = expander.expand("*.pdf")

        # Should only match the file, not the directory
        assert len(matches) == 1
        assert matches[0].is_file()

    def test_sorted_results(self, tmp_path: Path) -> None:
        """Test that results are sorted."""
        (tmp_path / "c.pdf").write_bytes(b"test")
        (tmp_path / "a.pdf").write_bytes(b"test")
        (tmp_path / "b.pdf").write_bytes(b"test")

        expander = GlobPatternExpander(tmp_path)
        matches = expander.expand("*.pdf")

        names = [f.name for f in matches]
        assert names == ["a.pdf", "b.pdf", "c.pdf"]


# ============================================================================
# IncrementalProcessor Tests
# ============================================================================


class TestIncrementalProcessor:
    """Tests for IncrementalProcessor orchestration."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test processor initialization."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        processor = IncrementalProcessor(
            source_dir=source_dir,
            output_dir=output_dir,
            config_hash="test_hash",
        )

        assert processor.source_dir == source_dir.resolve()
        assert processor.output_dir == output_dir.resolve()
        assert processor.config_hash == "test_hash"

    def test_analyze_no_state(self, tmp_path: Path) -> None:
        """Test analyze when no state exists (all files are new)."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        # Create test files
        (source_dir / "doc1.pdf").write_bytes(b"test1")
        (source_dir / "doc2.pdf").write_bytes(b"test2")

        processor = IncrementalProcessor(source_dir, output_dir)
        changes = processor.analyze()

        # All files should be new
        assert changes.new_count == 2
        assert changes.modified_count == 0
        assert changes.unchanged_count == 0

    def test_get_status_no_state(self, tmp_path: Path) -> None:
        """Test status when no state exists."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        processor = IncrementalProcessor(source_dir, output_dir)
        status = processor.get_status()

        assert status["total_files"] == 0
        assert status["last_updated"] is None
        assert status["sync_state"] == "not processed"

    def test_get_status_with_changes(self, tmp_path: Path) -> None:
        """Test status when changes are detected."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        # Create and process file
        test_file = source_dir / "doc.pdf"
        test_file.write_bytes(b"original")

        processor = IncrementalProcessor(source_dir, output_dir)
        processor.process()  # Process to create state

        # Modify file
        test_file.write_bytes(b"modified")

        # Create new processor to reload state from disk
        processor2 = IncrementalProcessor(source_dir, output_dir)

        # Get status
        status = processor2.get_status()

        assert status["total_files"] == 1
        assert "changes detected" in status["sync_state"]
        assert status["changes"]["modified"] == 1

    def test_process_force_mode(self, tmp_path: Path) -> None:
        """Test processing in force mode (reprocess all)."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        # Create files
        (source_dir / "doc1.pdf").write_bytes(b"test1")
        (source_dir / "doc2.pdf").write_bytes(b"test2")

        processor = IncrementalProcessor(source_dir, output_dir)

        # Process normally first
        result1 = processor.process()
        assert result1.successful == 2
        assert result1.skipped == 0

        # Process again with force=True
        result2 = processor.process(force=True)
        assert result2.successful == 2
        assert result2.skipped == 0  # Nothing skipped in force mode

    def test_process_incremental_mode(self, tmp_path: Path) -> None:
        """Test incremental processing (skip unchanged)."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        # Create files
        (source_dir / "doc1.pdf").write_bytes(b"test1")
        (source_dir / "doc2.pdf").write_bytes(b"test2")

        processor = IncrementalProcessor(source_dir, output_dir)

        # Process first time
        result1 = processor.process()
        assert result1.successful == 2

        # Create new processor to reload state from disk
        processor2 = IncrementalProcessor(source_dir, output_dir)

        # Process again without changes
        result2 = processor2.process()
        assert result2.skipped == 2  # Both files skipped
        assert result2.successful == 0  # Nothing to process

    def test_processing_result_structure(self) -> None:
        """Test ProcessingResult dataclass."""
        result = ProcessingResult(
            total_files=10,
            successful=8,
            failed=2,
            skipped=5,
            time_saved_estimate=25.0,
        )

        assert result.total_files == 10
        assert result.successful == 8
        assert result.failed == 2
        assert result.skipped == 5
        assert result.time_saved_estimate == 25.0
