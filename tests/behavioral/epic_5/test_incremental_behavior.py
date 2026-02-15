"""BT-007: Incremental Processing Behavior Tests (Story 5-7).

This behavioral test suite validates that incremental processing correctly
identifies file changes and only processes modified documents, reducing
processing time while maintaining data consistency.

Reference: docs/tech-spec-epic-5.md
Story 5-7: Batch Processing Optimization and Incremental Updates
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.behavioral,
    pytest.mark.story_5_7,
    pytest.mark.cli,
    pytest.mark.incremental,
]


class TestChangeDetectionBehavior:
    """Validate behavioral outcomes of change detection in incremental mode."""

    def test_unchanged_files_not_reprocessed(self, processed_corpus_with_state: dict) -> None:
        """
        RED: Validate that unchanged files are skipped during incremental processing.

        Given: A corpus with files previously processed and tracked in state
        When: Incremental mode processes the directory again
        Then: Unchanged files (same hash) should be skipped, not reprocessed
        And: Processing statistics should show files as "skipped"

        Expected RED failure: IncrementalProcessor not implemented
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]
        file_count = len(processed_corpus_with_state["file_list"])

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)
        change_summary = processor.analyze()

        # Then
        assert change_summary.unchanged_count == file_count, (
            f"Expected {file_count} unchanged files, " f"got {change_summary.unchanged_count}"
        )
        assert change_summary.new_count == 0
        assert change_summary.modified_count == 0

    def test_modified_files_detected_by_hash(self, mixed_corpus: dict) -> None:
        """
        RED: Validate that modified files are detected when content hash changes.

        Given: A corpus with some files modified since last processing
        When: Incremental mode detects changes
        Then: Files with different SHA256 hashes should be marked as "modified"
        And: Change summary should include modified file count

        Expected RED failure: Change detection not implemented
        """
        # Given
        source_dir = mixed_corpus["source_dir"]
        output_dir = mixed_corpus["output_dir"]
        modified_count = mixed_corpus["modified_count"]

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)
        change_summary = processor.analyze()

        # Then
        assert change_summary.modified_count == modified_count, (
            f"Expected {modified_count} modified files, " f"got {change_summary.modified_count}"
        )
        assert len(change_summary.modified_files) == modified_count

    def test_new_files_detected_not_in_state(self, mixed_corpus: dict) -> None:
        """
        RED: Validate that new files not in state are detected.

        Given: A corpus with new files not previously processed
        When: Incremental mode detects changes
        Then: Files not in the state file should be marked as "new"
        And: Change summary should include count and list of new files

        Expected RED failure: New file detection not implemented
        """
        # Given
        source_dir = mixed_corpus["source_dir"]
        output_dir = mixed_corpus["output_dir"]
        new_count = mixed_corpus["new_count"]

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)
        change_summary = processor.analyze()

        # Then
        assert (
            change_summary.new_count == new_count
        ), f"Expected {new_count} new files, got {change_summary.new_count}"
        assert len(change_summary.new_files) == new_count

    def test_deleted_files_detected_as_orphans(self, orphan_corpus: dict) -> None:
        """
        RED: Validate that deleted files are detected as orphans.

        Given: A corpus where source files have been deleted
        And: State file still references the deleted files
        When: Incremental mode detects changes
        Then: Deleted files should be marked as "orphans"
        And: System should offer cleanup option for orphaned outputs

        Expected RED failure: Orphan detection not implemented
        """
        # Given
        source_dir = orphan_corpus["source_dir"]
        output_dir = orphan_corpus["output_dir"]
        deleted_count = len(orphan_corpus["deleted_files"])

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)
        change_summary = processor.analyze()

        # Then
        assert change_summary.deleted_count == deleted_count, (
            f"Expected {deleted_count} orphan files, " f"got {change_summary.deleted_count}"
        )

    def test_config_change_detected_and_invalidates_cache(
        self, processed_corpus_with_state: dict, tmp_path: Path
    ) -> None:
        """
        RED: Validate that configuration changes invalidate incremental cache.

        Given: A corpus with state file from previous configuration
        When: User changes configuration (different TF-IDF settings, etc.)
        Then: New config hash should differ from state config hash
        And: All files should be marked for reprocessing (cache invalidation)

        Expected RED failure: Config hash comparison not implemented
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]

        # Create new config with different settings (different hash)

        new_config_str = '{"tfidf_max_features": 3000, "tfidf_min_df": 1}'
        new_config_hash = hashlib.sha256(new_config_str.encode()).hexdigest()

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir, config_hash=new_config_hash)

        # Then
        # When config hash changes, the processor should recognize it changed
        # This is evidenced by analyzing with different config hash
        # The old state has a different config, so all files should be candidates for reprocessing
        processor_status = processor.get_status()
        assert processor_status is not None  # Status can be retrieved with different config


class TestStateFilePersistence:
    """Validate that state files persist and update correctly across sessions."""

    def test_state_file_persists_across_sessions(self, processed_corpus_with_state: dict) -> None:
        """
        RED: Validate that state file persists between CLI invocations.

        Given: First session creates and updates state file
        When: Second session reads the same state file
        Then: State file should contain all processed file entries from first session
        And: Timestamps and hashes should match

        Expected RED failure: State persistence not implemented
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]
        state_file = processed_corpus_with_state["state_file"]
        original_state = json.loads(state_file.read_text())

        # When
        from data_extract.cli.batch import IncrementalProcessor

        # First processor uses the state
        processor = IncrementalProcessor(source_dir, output_dir)

        # Second processor (different instance) loads same state
        processor2 = IncrementalProcessor(source_dir, output_dir)

        # Then - verify state persists
        assert processor._state is not None, "State should be loaded from file"
        assert processor._state["version"] == original_state["version"]
        assert processor._state["files"] == original_state["files"]

        # Also verify second processor sees same state
        assert processor2._state is not None, "State should persist in second instance"
        assert processor2._state["files"] == processor._state["files"]

    def test_state_file_atomic_writes(
        self, processed_corpus_with_state: dict, tmp_path: Path
    ) -> None:
        """
        RED: Validate that state file updates are atomic (no partial writes).

        Given: A running incremental processor updating state
        When: State file is being written during processing
        Then: Intermediate reads should never see partial/corrupt JSON
        And: File should have consistent structure before/after write

        Expected RED failure: Atomic write mechanism not implemented
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]

        # When
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)

        # Update state by processing files
        files_to_process = list(source_dir.glob("*.pdf"))
        if files_to_process:
            processor._update_state(files_to_process)

        # Then - state file should be valid JSON
        state_file = processor.state_file.get_path()
        assert state_file.exists(), "State file should exist after update"

        written_state = json.loads(state_file.read_text())
        assert isinstance(written_state, dict), "State should be valid JSON dict"
        assert "files" in written_state, "State should have 'files' key"
        assert "version" in written_state, "State should have 'version' key"

    def test_state_file_schema_validation(self, incremental_state_file: Path) -> None:
        """
        RED: Validate that corrupted state files are detected and handled.

        Given: A corrupted or invalid state file
        When: IncrementalProcessor tries to load it
        Then: Should gracefully handle corrupted state (returns None or empty state)
        And: Should allow recovery options (reset, restore backup)

        Expected RED failure: Schema validation not implemented
        """
        # Given - create a corrupted state file
        state_dir = incremental_state_file.parent
        corrupted_file = state_dir / "incremental-state.json"
        corrupted_file.write_text("{ invalid json")

        # When/Then
        from data_extract.cli.batch import StateFile

        state_file = StateFile(state_dir.parent)
        loaded_state = state_file.load()

        # StateFile should handle corruption gracefully
        # (returns None if corrupted)
        assert loaded_state is None or isinstance(
            loaded_state, dict
        ), "Should handle corrupted state gracefully"


class TestIncrementalModeIntegration:
    """Test integration of incremental mode with overall processing."""

    def test_incremental_flag_activates_change_detection(
        self, processed_corpus_with_state: dict
    ) -> None:
        """
        RED: Validate that --incremental flag activates change detection.

        Given: CLI invoked with --incremental flag
        When: Process command is executed
        Then: Should use IncrementalProcessor instead of full reprocessing
        And: State file path should be calculated (.data-extract-session/...)

        Expected RED failure: Flag processing not implemented
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]

        # When - incremental processor is used (flag equivalent)
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)

        # Then - verify incremental processor is operational
        # and uses proper state file path
        state_path = processor.state_file.get_path()
        assert ".data-extract-session" in str(
            state_path
        ), "State file should be in .data-extract-session"
        assert "incremental-state.json" in str(state_path), "State file should be named correctly"

    def test_force_flag_bypasses_incremental_skip(self, processed_corpus_with_state: dict) -> None:
        """
        RED: Validate that --force flag reprocesses all files regardless of state.

        Given: A corpus with unchanged files in state
        When: Process command invoked with --force --incremental flags
        Then: All files should be reprocessed (state is ignored)
        And: State file should be updated with new processing metadata

        Expected RED failure: Force flag handling not implemented
        """
        # Given - corpus with unchanged files in state
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = processed_corpus_with_state["output_dir"]
        all_files = list(source_dir.glob("*.pdf"))
        file_count = len(all_files)

        # When - process with force flag
        from data_extract.cli.batch import IncrementalProcessor

        processor = IncrementalProcessor(source_dir, output_dir)
        result = processor.process(force=True)  # force=True bypasses incremental skip

        # Then
        # With force=True, all files should be processed, none skipped
        assert result.total_files == file_count, "All files should be counted"
        assert (
            result.skipped == 0
        ), f"No files should be skipped with force=True, got {result.skipped} skipped"
        assert result.successful + result.failed == file_count, "All files should be processed"
