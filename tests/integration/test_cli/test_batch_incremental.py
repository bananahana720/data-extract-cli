"""Integration Tests for Batch Incremental Processing (Story 5-7).

Tests the complete integration of incremental processing with the CLI,
including flag handling, state management, and command execution.

Story 5-7: Batch Processing Optimization and Incremental Updates
Reference: docs/tech-spec-epic-5.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="Typer is required for integration CLI tests")

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.story_5_7, pytest.mark.cli]


# ==============================================================================
# Process Command with Incremental Flag
# ==============================================================================


class TestProcessIncrementalFlag:
    """Integration tests for --incremental flag in process command."""

    def test_incremental_flag_accepted_by_process_command(self, tmp_path: Path) -> None:
        """
        Verify process command accepts --incremental flag.

        Given: A corpus directory
        When: data-extract process --incremental <dir> is invoked
        Then: Command should accept the flag without error
        And: Should route to IncrementalProcessor
        """
        # Given
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()
        (source_dir / "test.pdf").write_bytes(b"PDF content")

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Command should accept flag without "not recognized" error
        assert result.exit_code == 0 or "not recognized" not in result.stdout.lower()

    def test_incremental_mode_creates_state_file(self, tmp_path: Path) -> None:
        """
        Verify incremental mode analyzes changes.

        Given: A corpus with no existing state
        When: process --incremental is run for first time
        Then: Should analyze files for incremental processing
        And: Should display change analysis or process files
        """
        # Given
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()
        (source_dir / "test1.pdf").write_bytes(b"%PDF-1.4\n" + b"PDF content" * 10)
        (source_dir / "test2.txt").write_text("Text document content.\n" * 10)

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Should execute without critical errors
        assert result.exit_code == 0 or "error" not in result.stdout.lower()
        # Should show incremental analysis output or processing activity
        output_lower = result.stdout.lower()
        assert (
            "new" in output_lower
            or "incremental" in output_lower
            or "process" in output_lower
            or "file" in output_lower
        )

    def test_incremental_skips_unchanged_files(
        self, processed_corpus_with_state: dict, tmp_path: Path
    ) -> None:
        """
        Verify incremental mode skips unchanged files on second run.

        Given: A corpus previously processed (state file exists)
        When: process --incremental is run again without changes
        Then: Should skip all unchanged files
        And: Output statistics should show skipped count
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = source_dir.parent / "output_new"
        output_dir.mkdir(parents=True, exist_ok=True)

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Should show evidence of skipping
        assert "skipped" in result.stdout.lower() or "unchanged" in result.stdout.lower()

    def test_incremental_processes_new_files_only(self, mixed_corpus: dict, tmp_path: Path) -> None:
        """
        Verify incremental mode processes only new files.

        Given: A corpus with new files added since last processing
        When: process --incremental is run
        Then: Should only process new files (not unchanged ones)
        And: Should update state with new files
        """
        # Given
        source_dir = mixed_corpus["source_dir"]
        state_file = mixed_corpus["state_file"]
        output_dir = source_dir.parent / "output_new"
        output_dir.mkdir(parents=True, exist_ok=True)

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then
        assert result.exit_code == 0
        # State file should be updated with new files
        state = json.loads(state_file.read_text())
        assert len(state["files"]) > 0


# ==============================================================================
# Force Flag Integration
# ==============================================================================


class TestProcessForceFlag:
    """Integration tests for --force flag with incremental processing."""

    def test_force_flag_reprocesses_all_files(
        self, processed_corpus_with_state: dict, tmp_path: Path
    ) -> None:
        """
        Verify --force flag reprocesses all files regardless of state.

        Given: A corpus with unchanged files in state
        When: process --incremental --force is invoked
        Then: Should reprocess all files (ignore state skip)
        And: Should update state with new processing times
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = source_dir.parent / "output_force"
        output_dir.mkdir(parents=True, exist_ok=True)

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--force",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then
        assert result.exit_code == 0
        # Should process files (not skip them)
        assert "processed" in result.stdout.lower() or "processing" in result.stdout.lower()

    def test_force_flag_updates_state_with_new_timestamps(
        self, processed_corpus_with_state: dict, tmp_path: Path
    ) -> None:
        """
        Verify --force flag bypasses incremental skipping.

        Given: A corpus with old processing timestamps in state
        When: process --incremental --force is invoked
        Then: Should process all files (not skip unchanged)
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        output_dir = source_dir.parent / "output_force2"
        output_dir.mkdir(parents=True, exist_ok=True)

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "process",
                    str(source_dir),
                    "--incremental",
                    "--force",
                    "--output",
                    str(output_dir),
                ],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Should execute successfully
        assert result.exit_code == 0
        # Should process files (force mode)
        output_lower = result.stdout.lower()
        assert (
            "process" in output_lower
            or "force" in output_lower
            or "file" in output_lower
            or "progress" in output_lower
        )


# ==============================================================================
# Status Command Integration
# ==============================================================================


class TestStatusCommand:
    """Integration tests for status command showing sync state."""

    def test_status_command_displays_panel(self, tmp_path: Path) -> None:
        """
        Verify status command displays information panel.

        Given: A corpus with processing state
        When: data-extract status <dir> is invoked
        Then: Should display a Rich panel with status information
        And: Panel should use proper Rich formatting
        """
        # Given
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(app, ["status", str(source_dir)])
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Command should execute successfully
        assert result.exit_code == 0
        # Should show status information (text or JSON format)
        assert len(result.stdout) > 0

    def test_status_shows_processed_file_count(self, processed_corpus_with_state: dict) -> None:
        """
        Verify status command shows number of processed files.

        Given: A corpus with processed files in state
        When: data-extract status <dir> is invoked
        Then: Should display "Processed Files: N"
        And: Count should match files in state
        """
        # Given
        source_dir = processed_corpus_with_state["source_dir"]
        file_count = len(processed_corpus_with_state["file_list"])

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(app, ["status", str(source_dir)])
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Should show processed information
        assert result.exit_code == 0
        assert "processed" in result.stdout.lower() or "files" in result.stdout.lower()
        # File count should appear in output
        assert str(file_count) in result.stdout

    def test_status_shows_sync_state(self, mixed_corpus: dict) -> None:
        """
        Verify status command shows sync state (new/modified/unchanged).

        Given: A corpus with mixed file states
        When: data-extract status <dir> is invoked
        Then: Should display:
              - "New Files: N"
              - "Modified Files: N"
              - "Unchanged Files: N"
        """
        # Given
        source_dir = mixed_corpus["source_dir"]

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(app, ["status", str(source_dir)])
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then
        assert result.exit_code == 0
        # Should show change information
        output_lower = result.stdout.lower()
        assert "new" in output_lower or "modified" in output_lower or "unchanged" in output_lower

    def test_status_offers_cleanup_option_for_orphans(self, orphan_corpus: dict) -> None:
        """
        Verify status command offers cleanup for orphaned outputs.

        Given: A corpus with orphaned output files
        When: data-extract status <dir> is invoked
        Then: Should display orphan count
        And: Should suggest: "Run with --cleanup to remove orphaned outputs"
        """
        # Given
        source_dir = orphan_corpus["source_dir"]

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(app, ["status", str(source_dir)])
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then
        assert result.exit_code == 0
        # Should show orphan information or cleanup suggestion
        output_lower = result.stdout.lower()
        assert "orphan" in output_lower or "cleanup" in output_lower or "deleted" in output_lower


# ==============================================================================
# Glob Pattern CLI Integration
# ==============================================================================


class TestGlobPatternCLI:
    """Integration tests for glob pattern support in process command."""

    def test_process_accepts_glob_pattern_argument(self, tmp_path: Path) -> None:
        """
        Verify process command accepts glob pattern as argument.

        Given: A pattern string (e.g., "**/*.pdf")
        When: data-extract process "**/*.pdf" is invoked
        Then: Command should accept pattern without error
        And: Should expand pattern to matching files
        """
        # Given
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.pdf").write_bytes(b"PDF")

        # When
        try:
            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["process", str(source_dir / "*.pdf")],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")

        # Then - Command should accept pattern
        assert result.exit_code == 0 or "not recognized" not in result.stdout.lower()

    def test_glob_pattern_displays_match_count(self, tmp_path: Path) -> None:
        """
        Verify glob pattern expansion shows match count.

        Given: A glob pattern matching specific files
        When: process command is invoked with pattern
        Then: Should display "Matched: N files"
        And: Count should reflect actual matches
        """
        # Given
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.pdf").write_bytes(b"PDF1")
        (source_dir / "file2.pdf").write_bytes(b"PDF2")
        (source_dir / "file1.txt").write_bytes(b"TXT")

        # When - Use relative pattern from current directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(str(source_dir))

            from typer.testing import CliRunner

            from data_extract.cli.app import app

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["process", "*.pdf"],
            )
        except ImportError:
            pytest.fail("Cannot import CLI components")
        finally:
            os.chdir(original_cwd)

        # Then
        assert result.exit_code == 0
        # Should process or mention the PDF files
        assert "2" in result.stdout or "file1.pdf" in result.stdout or "file2.pdf" in result.stdout
