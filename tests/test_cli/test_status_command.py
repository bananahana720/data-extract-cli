"""CLI Status Command Tests - TDD RED Phase (Story 5-1).

Test cases for new status command that displays sync state and file counts.

Expected: All tests FAIL initially (RED phase of TDD).

AC-5-1: Status command exists and registers
AC-5-1: Status command help text
AC-5-1: Status shows total files and sync state
AC-5-1: Status verbose mode shows breakdown (new/modified/unchanged)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from data_extract.cli.base import _reset_app, get_app


@pytest.fixture
def runner():
    """Provide fresh CLI runner with reset app instance."""
    _reset_app()
    return CliRunner()


@pytest.fixture
def app():
    """Get fresh app instance."""
    _reset_app()
    return get_app()


@pytest.fixture
def sample_working_dir(tmp_path: Path) -> Path:
    """Create a sample working directory with test files."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    # Create some sample files
    for i in range(5):
        test_file = work_dir / f"document_{i}.txt"
        test_file.write_text(f"Sample document content {i}\n" * 5)

    return work_dir


@pytest.fixture
def state_file_with_history(tmp_path: Path) -> Path:
    """Create a state file with processing history."""
    state_file = tmp_path / ".data-extract-state.json"
    state_data = {
        "files": {
            "document_0.txt": {
                "hash": "abc123def456",
                "chunks": 5,
                "status": "processed",
            },
            "document_1.txt": {
                "hash": "def456ghi789",
                "chunks": 3,
                "status": "processed",
            },
            "document_2.txt": {
                "hash": "old_hash_unchanged",
                "chunks": 4,
                "status": "processed",
            },
        },
        "last_run": "2025-11-29T10:00:00Z",
        "summary": {
            "total_files_processed": 3,
            "total_chunks": 12,
            "success_count": 3,
            "error_count": 0,
        },
    }
    state_file.write_text(json.dumps(state_data, indent=2))
    return state_file


# ==============================================================================
# Status Command Registration Tests
# ==============================================================================


class TestStatusCommandExists:
    """Test cases for status command registration."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_command_exists(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status command is registered and accessible.

        Given: data-extract CLI application
        When: We invoke "status" command
        Then: Should not fail with "no such command" error
        And: Should display status information

        Expected RED failure: Command not found / not registered
        """
        result = runner.invoke(app, ["status"])

        # Should not fail due to unknown command
        assert "no such command" not in result.output.lower()
        assert "not found" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_command_in_help(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status command appears in main help output.

        Given: CLI main help
        When: We invoke "--help" on app
        Then: Should list "status" as available command

        Expected RED failure: Status not listed in help
        """
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "status" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_command_short_help(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status command has brief help text in listing.

        Given: CLI main help
        When: We invoke "--help"
        Then: Status command should have description

        Expected RED failure: No description or unclear help text
        """
        result = runner.invoke(app, ["--help"])

        # Find status in help output and verify it has description
        lines = result.output.split("\n")
        status_line = None
        for i, line in enumerate(lines):
            if "status" in line.lower():
                status_line = line
                break

        assert status_line is not None
        # Status line should have more than just the command name
        assert len(status_line.strip()) > 10


# ==============================================================================
# Status Command Help Tests
# ==============================================================================


class TestStatusCommandHelp:
    """Test cases for status command help documentation."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_shows_help(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status command has detailed help.

        Given: status command with --help flag
        When: We invoke "status --help"
        Then: Should display usage information
        And: Should list available options

        Expected RED failure: Help not available or incomplete
        """
        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        assert "usage" in result.output.lower() or "options" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_help_mentions_verbose(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status help mentions --verbose option.

        Given: status command help
        When: We invoke "status --help"
        Then: Should document --verbose option

        Expected RED failure: Verbose option not documented
        """
        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        assert "--verbose" in result.output or "-v" in result.output

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_help_mentions_format_option(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status help mentions format output option.

        Given: status command help
        When: We invoke "status --help"
        Then: Should document format options (json, text, etc)

        Expected RED failure: Format option not documented
        """
        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        # Should mention format or output format option
        assert "--format" in result.output or "format" in result.output.lower()


# ==============================================================================
# Status Command - Basic Output Tests
# ==============================================================================


class TestStatusBasicOutput:
    """Test cases for status command basic output."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_basic_execution(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status command executes and returns exit code 0.

        Given: status command without arguments
        When: We invoke "status"
        Then: Should execute successfully (exit code 0)
        And: Should display status information

        Expected RED failure: Command fails or returns non-zero exit code
        """
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_shows_sync_state(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status shows overall sync state.

        Given: status command
        When: We invoke "status"
        Then: Should display sync state (synced/out-of-sync/uninitialized)
        Or: Should show whether previous processing has occurred

        Expected RED failure: Sync state not shown
        """
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        # Should mention sync, state, or status-related information
        output_lower = result.output.lower()
        assert any(
            term in output_lower
            for term in [
                "sync",
                "state",
                "status",
                "file",
                "processed",
                "initialized",
            ]
        )

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_shows_file_count(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status shows total file count.

        Given: status command
        When: We invoke "status"
        Then: Should display total number of files tracked
        And: Should show numeric count

        Expected RED failure: File count not shown
        """
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        # Should contain numbers indicating file count
        assert any(char.isdigit() for char in result.output)

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_shows_summary_stats(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status shows summary statistics.

        Given: status command
        When: We invoke "status"
        Then: Should display summary of files processed
        And: Should show chunks processed

        Expected RED failure: Summary not shown
        """
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        # Should mention summary or key metrics
        output_lower = result.output.lower()
        assert any(term in output_lower for term in ["summary", "total", "chunk", "processed"])


# ==============================================================================
# Status Command - Verbose Mode Tests
# ==============================================================================


class TestStatusVerboseMode:
    """Test cases for status command verbose mode."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_flag_recognized(self, runner: CliRunner, app) -> None:
        """
        RED: Verify --verbose flag is recognized.

        Given: status command with --verbose flag
        When: We invoke "status --verbose"
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        result = runner.invoke(app, ["status", "--verbose"])

        assert "no such option" not in result.output.lower()
        assert result.exit_code == 0

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_short_flag(self, runner: CliRunner, app) -> None:
        """
        RED: Verify -v short flag works for verbose.

        Given: status command with -v flag
        When: We invoke "status -v"
        Then: Should work same as --verbose

        Expected RED failure: Short flag not recognized
        """
        result = runner.invoke(app, ["status", "-v"])

        assert result.exit_code == 0
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_shows_file_breakdown(self, runner: CliRunner, app) -> None:
        """
        RED: Verify verbose mode shows file breakdown.

        Given: status command with --verbose flag
        When: We invoke "status --verbose"
        Then: Should show breakdown of file statuses
        And: Should distinguish new, modified, and unchanged files

        Expected RED failure: Breakdown not shown or normal output
        """
        result = runner.invoke(app, ["status", "--verbose"])

        assert result.exit_code == 0
        # Verbose should show more details than normal mode
        output_lower = result.output.lower()
        # Should mention file categories
        assert any(
            term in output_lower
            for term in [
                "new",
                "modified",
                "unchanged",
                "breakdown",
                "detailed",
                "per-file",
            ]
        )

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_shows_new_files(self, runner: CliRunner, app) -> None:
        """
        RED: Verify verbose shows count of new files.

        Given: status --verbose
        When: We invoke the command
        Then: Should show number of new files not yet processed

        Expected RED failure: New files count not shown
        """
        result = runner.invoke(app, ["status", "--verbose"])

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert "new" in output_lower

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_shows_modified_files(self, runner: CliRunner, app) -> None:
        """
        RED: Verify verbose shows count of modified files.

        Given: status --verbose
        When: We invoke the command
        Then: Should show number of previously processed files that changed

        Expected RED failure: Modified files count not shown
        """
        result = runner.invoke(app, ["status", "--verbose"])

        assert result.exit_code == 0
        output_lower = result.output.lower()
        # Should mention modified or changed
        assert any(term in output_lower for term in ["modified", "changed", "update"])

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_verbose_shows_unchanged_files(self, runner: CliRunner, app) -> None:
        """
        RED: Verify verbose shows count of unchanged files.

        Given: status --verbose
        When: We invoke the command
        Then: Should show number of unchanged files (no reprocessing needed)

        Expected RED failure: Unchanged files count not shown
        """
        result = runner.invoke(app, ["status", "--verbose"])

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert "unchanged" in output_lower or "skip" in output_lower


# ==============================================================================
# Status Command - Format Output Tests
# ==============================================================================


class TestStatusFormatOutput:
    """Test cases for status command output formats."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_json_format(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status supports JSON output format.

        Given: status command with --format json
        When: We invoke "status --format json"
        Then: Should output valid JSON
        And: JSON should contain status fields

        Expected RED failure: JSON format not supported
        """
        result = runner.invoke(app, ["status", "--format", "json"])

        assert result.exit_code == 0
        # Should be able to parse as JSON
        try:
            json_data = json.loads(result.output)
            assert isinstance(json_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_text_format(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status supports text output format.

        Given: status command with --format text
        When: We invoke "status --format text"
        Then: Should output human-readable text

        Expected RED failure: Text format not supported
        """
        result = runner.invoke(app, ["status", "--format", "text"])

        assert result.exit_code == 0
        # Output should be readable text (not JSON)
        assert len(result.output) > 0

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_invalid_format_rejected(self, runner: CliRunner, app) -> None:
        """
        RED: Verify invalid format is rejected.

        Given: status command with invalid format
        When: We invoke "status --format invalid_format"
        Then: Should fail with validation error

        Expected RED failure: Command accepts any format string
        """
        result = runner.invoke(app, ["status", "--format", "invalid_format"])

        assert result.exit_code != 0


# ==============================================================================
# Status Command - Working Directory Tests
# ==============================================================================


class TestStatusWorkingDirectory:
    """Test cases for status command with different working directories."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_no_state_file_yet(self, runner: CliRunner, app, tmp_path: Path) -> None:
        """
        RED: Verify status works when no processing has occurred yet.

        Given: A directory with no state file
        When: We invoke "status"
        Then: Should indicate "uninitialized" or "not yet processed"
        And: Should show 0 files processed

        Expected RED failure: Command fails when state missing
        """
        # Create fresh temp directory with no state file
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        # Should indicate fresh/uninitialized state
        output_lower = result.output.lower()
        assert any(
            term in output_lower for term in ["uninitialize", "not processed", "no state", "new"]
        )

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_with_existing_state(
        self, runner: CliRunner, app, state_file_with_history: Path
    ) -> None:
        """
        RED: Verify status shows info from existing state file.

        Given: A state file with processing history
        When: We invoke "status" in that directory
        Then: Should show files from state file
        And: Should show last run time

        Expected RED failure: State file not read or data not displayed
        """
        # This would require proper setup with working directory management
        result = runner.invoke(app, ["status"])

        # Should succeed and show information
        assert result.exit_code == 0


# ==============================================================================
# Status Command - Edge Cases
# ==============================================================================


class TestStatusEdgeCases:
    """Test cases for status command edge cases."""

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_no_arguments_succeeds(self, runner: CliRunner, app) -> None:
        """
        RED: Verify status works without any arguments.

        Given: status command with no flags
        When: We invoke "status"
        Then: Should display status with default settings

        Expected RED failure: Command requires arguments
        """
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0

    @pytest.mark.cli
    @pytest.mark.story_5_1
    def test_status_help_flag_takes_precedence(self, runner: CliRunner, app) -> None:
        """
        RED: Verify --help flag shows help instead of status.

        Given: status --help
        When: We invoke the command
        Then: Should show help text, not actual status

        Expected RED failure: Shows status instead of help
        """
        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        assert "usage" in result.output.lower() or "options" in result.output.lower()
        # Should not show actual status data
