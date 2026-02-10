"""Quick verification tests for Story 5-7 fixtures.

This test file verifies that the fixture implementations work correctly
by accessing their structure and validating key properties.

These tests will be removed once the actual Story 5-7 tests are implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.P0, pytest.mark.integration, pytest.mark.story_5_7, pytest.mark.cli]


class TestProcessedCorpusWithStateFixture:
    """Verify processed_corpus_with_state fixture works correctly."""

    @pytest.mark.test_id("int-INT-001")
    def test_fixture_creates_source_directory(self, processed_corpus_with_state: dict) -> None:
        """Verify fixture creates source directory."""
        source_dir = processed_corpus_with_state["source_dir"]
        assert source_dir.exists(), "Source directory should exist"
        assert source_dir.is_dir(), "Source directory should be a directory"

    @pytest.mark.test_id("int-INT-002")
    def test_fixture_creates_state_file(self, processed_corpus_with_state: dict) -> None:
        """Verify fixture creates state file."""
        state_file = processed_corpus_with_state["state_file"]
        assert state_file.exists(), "State file should exist"
        assert state_file.suffix == ".json", "State file should be JSON format"

    @pytest.mark.test_id("int-INT-003")
    def test_fixture_state_file_is_valid_json(self, processed_corpus_with_state: dict) -> None:
        """Verify state file contains valid JSON."""
        state_file = processed_corpus_with_state["state_file"]
        state_content = state_file.read_text()
        state = json.loads(state_content)
        assert isinstance(state, dict), "State file should contain a dictionary"

    @pytest.mark.test_id("int-INT-004")
    def test_fixture_state_has_required_fields(self, processed_corpus_with_state: dict) -> None:
        """Verify state file has required fields."""
        state_file = processed_corpus_with_state["state_file"]
        state = json.loads(state_file.read_text())

        assert "version" in state, "State should have version field"
        assert state["version"] == "1.0", "Version should be 1.0"
        assert "source_dir" in state, "State should have source_dir field"
        assert "output_dir" in state, "State should have output_dir field"
        assert "processed_at" in state, "State should have processed_at field"
        assert "files" in state, "State should have files field"

    @pytest.mark.test_id("int-INT-005")
    def test_fixture_creates_multiple_files(self, processed_corpus_with_state: dict) -> None:
        """Verify fixture creates 3+ test files."""
        file_list = processed_corpus_with_state["file_list"]
        assert len(file_list) >= 3, "Fixture should create at least 3 files"

        for file_path in file_list:
            assert file_path.exists(), f"File {file_path} should exist"
            assert file_path.is_file(), f"Path {file_path} should be a file"

    @pytest.mark.test_id("int-INT-006")
    def test_fixture_all_files_are_in_state(self, processed_corpus_with_state: dict) -> None:
        """Verify all created files are tracked in state."""
        state_file = processed_corpus_with_state["state_file"]
        file_list = processed_corpus_with_state["file_list"]

        state = json.loads(state_file.read_text())
        state_files = state["files"]

        for file_path in file_list:
            assert str(file_path) in state_files, f"File {file_path} should be in state"

    @pytest.mark.test_id("int-INT-007")
    def test_fixture_each_file_has_hash(self, processed_corpus_with_state: dict) -> None:
        """Verify each file entry in state has a hash."""
        state_file = processed_corpus_with_state["state_file"]
        state = json.loads(state_file.read_text())

        for file_path, file_info in state["files"].items():
            assert "hash" in file_info, f"File {file_path} should have a hash"
            assert len(file_info["hash"]) > 0, f"Hash for {file_path} should not be empty"


class TestMixedCorpusFixture:
    """Verify mixed_corpus fixture works correctly."""

    @pytest.mark.test_id("int-INT-008")
    def test_fixture_creates_source_directory(self, mixed_corpus: dict) -> None:
        """Verify fixture creates source directory."""
        source_dir = mixed_corpus["source_dir"]
        assert source_dir.exists(), "Source directory should exist"

    @pytest.mark.test_id("int-INT-009")
    def test_fixture_creates_state_file(self, mixed_corpus: dict) -> None:
        """Verify fixture creates state file."""
        state_file = mixed_corpus["state_file"]
        assert state_file.exists(), "State file should exist"

    @pytest.mark.test_id("int-INT-010")
    def test_fixture_has_new_files(self, mixed_corpus: dict) -> None:
        """Verify fixture creates new files (not in state)."""
        new_files = mixed_corpus["new_files"]
        assert len(new_files) > 0, "Should have new files"

        for file_path in new_files:
            assert file_path.exists(), f"New file {file_path} should exist"

    @pytest.mark.test_id("int-INT-011")
    def test_fixture_has_unchanged_files(self, mixed_corpus: dict) -> None:
        """Verify fixture creates unchanged files (in state with same hash)."""
        unchanged_files = mixed_corpus["unchanged_files"]
        assert len(unchanged_files) > 0, "Should have unchanged files"

        for file_path in unchanged_files:
            assert file_path.exists(), f"Unchanged file {file_path} should exist"

    @pytest.mark.test_id("int-INT-012")
    def test_fixture_has_modified_files(self, mixed_corpus: dict) -> None:
        """Verify fixture creates modified files (in state but changed)."""
        modified_files = mixed_corpus["modified_files"]
        assert len(modified_files) > 0, "Should have modified files"

        for file_path in modified_files:
            assert file_path.exists(), f"Modified file {file_path} should exist"

    @pytest.mark.test_id("int-INT-013")
    def test_fixture_modified_files_have_different_hash(self, mixed_corpus: dict) -> None:
        """Verify modified files have different hash than in state."""
        state_file = mixed_corpus["state_file"]
        modified_files = mixed_corpus["modified_files"]

        state = json.loads(state_file.read_text())
        state_files = state["files"]

        for file_path in modified_files:
            file_hash = self._compute_file_hash(file_path)
            state_hash = state_files[str(file_path)]["hash"]

            assert (
                file_hash != state_hash
            ), f"Modified file {file_path} should have different hash than state"

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        import hashlib

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()


class TestOrphanCorpusFixture:
    """Verify orphan_corpus fixture works correctly."""

    @pytest.mark.test_id("int-INT-014")
    def test_fixture_creates_source_directory(self, orphan_corpus: dict) -> None:
        """Verify fixture creates source directory."""
        source_dir = orphan_corpus["source_dir"]
        assert source_dir.exists(), "Source directory should exist"

    @pytest.mark.test_id("int-INT-015")
    def test_fixture_creates_state_file(self, orphan_corpus: dict) -> None:
        """Verify fixture creates state file."""
        state_file = orphan_corpus["state_file"]
        assert state_file.exists(), "State file should exist"

    @pytest.mark.test_id("int-INT-016")
    def test_fixture_has_existing_files(self, orphan_corpus: dict) -> None:
        """Verify fixture creates files that still exist."""
        existing_files = orphan_corpus["existing_files"]
        assert len(existing_files) > 0, "Should have existing files"

        for file_path in existing_files:
            assert file_path.exists(), f"Existing file {file_path} should exist"

    @pytest.mark.test_id("int-INT-017")
    def test_fixture_has_orphaned_file_paths(self, orphan_corpus: dict) -> None:
        """Verify fixture has orphaned file paths (in state but not on disk)."""
        orphaned_file_paths = orphan_corpus["orphaned_file_paths"]
        assert len(orphaned_file_paths) > 0, "Should have orphaned file paths"

        for file_path in orphaned_file_paths:
            assert (
                not file_path.exists()
            ), f"Orphaned file path {file_path} should NOT exist on disk"

    @pytest.mark.test_id("int-INT-018")
    def test_fixture_orphaned_files_in_state(self, orphan_corpus: dict) -> None:
        """Verify orphaned files are tracked in state."""
        state_file = orphan_corpus["state_file"]
        orphaned_file_paths = orphan_corpus["orphaned_file_paths"]

        state = json.loads(state_file.read_text())
        state_files = state["files"]

        for file_path in orphaned_file_paths:
            assert str(file_path) in state_files, f"Orphaned file {file_path} should be in state"

    @pytest.mark.test_id("int-INT-019")
    def test_fixture_has_orphaned_output_files(self, orphan_corpus: dict) -> None:
        """Verify fixture has orphaned output files."""
        orphaned_output_files = orphan_corpus["orphaned_output_files"]
        assert len(orphaned_output_files) > 0, "Should have orphaned output files"

        for file_path in orphaned_output_files:
            assert file_path.exists(), f"Orphaned output file {file_path} should exist"
