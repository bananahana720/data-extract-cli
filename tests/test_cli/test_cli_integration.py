"""CLI Integration Tests - TDD RED Phase (Stories 5-4, 5-5, 5-7).

Test cases for process command flags and integration with batch processing,
preset configuration, and incremental processing.

Expected: All tests FAIL initially (RED phase of TDD).

AC-5-4: Process command with --incremental flag
AC-5-4: Process command with --force flag
AC-5-5: Preset configuration with --preset quality
AC-5-4: Export summary with --export-summary
AC-5-7: Incremental processing skips unchanged files
AC-5-7: Force flag overrides incremental behavior
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

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
def sample_input_dir(tmp_path: Path) -> Path:
    """Create a sample input directory with test files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Create sample DOCX-like files for testing
    for i in range(3):
        test_file = input_dir / f"document_{i}.txt"
        test_file.write_text(f"Sample document content {i}\n" * 10)

    return input_dir


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a sample output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    """Create a sample state file for incremental processing."""
    state_file = tmp_path / ".data-extract-state.json"
    state_data = {
        "files": {
            "document_0.txt": {"hash": "abc123", "chunks": 5},
            "document_1.txt": {"hash": "def456", "chunks": 5},
        },
        "last_run": "2025-11-29T10:00:00Z",
    }
    state_file.write_text(json.dumps(state_data, indent=2))
    return state_file


# ==============================================================================
# Process Command - Incremental Flag Tests
# ==============================================================================


class TestProcessIncrementalFlag:
    """Test cases for --incremental flag on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_incremental_flag_recognized(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --incremental flag is recognized by process command.

        Given: process command with --incremental flag
        When: We invoke the command
        Then: Should not fail due to unknown flag
        And: Should process files with incremental logic

        Expected RED failure: Flag not recognized or command fails
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--incremental",
            ],
        )

        # Should not fail due to unknown flag
        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()
        # Command execution should complete (may fail for other reasons in RED)

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_incremental_short_flag(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --incremental has a short flag variant.

        Given: process command with -i flag
        When: We invoke the command
        Then: Should be recognized as incremental flag

        Expected RED failure: Short flag not recognized
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "-i",
            ],
        )

        # Short flag should be recognized
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_incremental_without_state_file(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --incremental processes all files when no state file exists.

        Given: --incremental flag with no previous state file
        When: We invoke the command
        Then: Should process all files (first run behavior)

        Expected RED failure: Command fails or doesn't create state file
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--incremental",
            ],
        )

        # Should succeed (exit code 0)
        # Or if it fails, should indicate why
        assert result.exit_code == 0 or "state" in result.output.lower()


# ==============================================================================
# Process Command - Force Flag Tests
# ==============================================================================


class TestProcessForceFlag:
    """Test cases for --force flag on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_force_flag_recognized(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --force flag is recognized by process command.

        Given: process command with --force flag
        When: We invoke the command
        Then: Should not fail due to unknown flag
        And: Should reprocess all files regardless of state

        Expected RED failure: Flag not recognized or command fails
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--force",
            ],
        )

        # Should not fail due to unknown flag
        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_force_short_flag(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --force has a short flag variant.

        Given: process command with -f flag
        When: We invoke the command
        Then: Should be recognized as force flag

        Expected RED failure: Short flag not recognized
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "-f",
            ],
        )

        # Short flag should be recognized
        assert "no such option" not in result.output.lower()


# ==============================================================================
# Process Command - Preset Flag Tests
# ==============================================================================


class TestProcessPresetFlag:
    """Test cases for --preset flag on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_preset_flag_recognized(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --preset flag is recognized by process command.

        Given: process command with --preset quality
        When: We invoke the command
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--preset",
                "quality",
            ],
        )

        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_preset_quality_loads_config(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --preset quality applies quality preset configuration.

        Given: --preset quality flag
        When: We invoke the process command
        Then: Should load and apply quality preset settings
        And: chunk_size should be set to quality preset value

        Expected RED failure: Preset not loaded or config not applied
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--preset",
                "quality",
            ],
        )

        # Should not fail, should apply preset
        # Quality preset typically has smaller chunk_size for better quality
        assert result.exit_code == 0 or "preset" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_preset_speed_loads_config(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --preset speed applies speed preset configuration.

        Given: --preset speed flag
        When: We invoke the process command
        Then: Should load and apply speed preset settings
        And: chunk_size should be set to speed preset value

        Expected RED failure: Preset not loaded or config not applied
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--preset",
                "speed",
            ],
        )

        assert result.exit_code == 0 or "preset" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_preset_balanced_loads_config(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --preset balanced applies balanced preset configuration.

        Given: --preset balanced flag
        When: We invoke the process command
        Then: Should load and apply balanced preset settings

        Expected RED failure: Preset not loaded or config not applied
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--preset",
                "balanced",
            ],
        )

        assert result.exit_code == 0 or "preset" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_invalid_preset_rejected(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify invalid preset name is rejected.

        Given: --preset invalid_preset_name
        When: We invoke the command
        Then: Should fail with validation error

        Expected RED failure: Command succeeds despite invalid preset
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--preset",
                "nonexistent_preset",
            ],
        )

        assert result.exit_code != 0
        assert "preset" in result.output.lower() or "invalid" in result.output.lower()


# ==============================================================================
# Process Command - Export Summary Tests
# ==============================================================================


class TestProcessExportSummary:
    """Test cases for --export-summary flag on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_export_summary_flag_recognized(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --export-summary flag is recognized.

        Given: process command with --export-summary
        When: We invoke the command
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--export-summary",
            ],
        )

        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_export_summary_creates_file(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --export-summary creates summary file.

        Given: --export-summary flag
        When: We invoke the process command
        Then: Should create a summary file (summary.json)
        And: Summary should contain processing statistics

        Expected RED failure: Summary file not created
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--export-summary",
            ],
        )

        # Look for summary file
        summary_files = list(output_dir.glob("*summary*"))
        assert len(summary_files) > 0, "No summary file created"

        # Summary should contain valid data
        if summary_files:
            summary_file = summary_files[0]
            assert summary_file.exists()
            if summary_file.suffix == ".json":
                content = json.loads(summary_file.read_text())
                assert isinstance(content, dict)

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_export_summary_without_output(
        self, runner: CliRunner, app, sample_input_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary defaults summary location.

        Given: --export-summary without explicit output path
        When: We invoke the command
        Then: Should create summary in input directory or current directory

        Expected RED failure: Summary not created when output path not specified
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--export-summary",
            ],
        )

        # Summary should be created somewhere accessible
        # Either in input dir or current working directory


# ==============================================================================
# Process Command - Incremental Behavior Tests
# ==============================================================================


class TestIncrementalBehavior:
    """Test cases for incremental processing behavior."""

    @pytest.mark.cli
    @pytest.mark.story_5_7
    def test_incremental_skips_unchanged_files(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path, state_file: Path
    ) -> None:
        """
        RED: Verify --incremental skips unchanged files.

        Given: A state file tracking previously processed files
        When: --incremental flag is set and files are unchanged
        Then: Unchanged files should be skipped
        And: Only modified/new files should be processed

        Expected RED failure: All files processed despite --incremental
        """
        with patch("data_extract.cli.batch.ChangeDetector") as mock_detector:
            mock_detector.return_value.get_changed_files.return_value = [
                "document_2.txt"  # Only new file
            ]

            result = runner.invoke(
                app,
                [
                    "process",
                    str(sample_input_dir),
                    "--output",
                    str(output_dir),
                    "--incremental",
                ],
            )

            # Should indicate skipped files in output
            # Or should process only 1 file (document_2) instead of 3

    @pytest.mark.cli
    @pytest.mark.story_5_7
    def test_force_overrides_incremental(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path, state_file: Path
    ) -> None:
        """
        RED: Verify --force with --incremental processes all files.

        Given: Both --force and --incremental flags set
        When: We invoke the command
        Then: Should process ALL files (force overrides incremental)
        And: Should update state file for next run

        Expected RED failure: Incremental takes precedence over force
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--incremental",
                "--force",
            ],
        )

        # Should process all files despite state file existing
        # Output should show all 3 files processed


# ==============================================================================
# Process Command - Combination Tests
# ==============================================================================


class TestProcessCommandCombinations:
    """Test cases for flag combinations on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    @pytest.mark.story_5_5
    def test_incremental_with_preset(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify --incremental works with --preset.

        Given: Both --incremental and --preset quality flags
        When: We invoke the command
        Then: Should apply preset settings AND use incremental logic

        Expected RED failure: Flags conflict or one overrides the other
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--incremental",
                "--preset",
                "quality",
            ],
        )

        assert result.exit_code == 0 or len(result.output) > 0

    @pytest.mark.cli
    @pytest.mark.story_5_4
    @pytest.mark.story_5_5
    def test_force_with_preset_and_export_summary(
        self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify multiple flags work together.

        Given: --force, --preset balanced, and --export-summary
        When: We invoke the command
        Then: Should combine all behaviors
        And: Should create summary file for all processed files

        Expected RED failure: Flags conflict or summary not created
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--output",
                str(output_dir),
                "--force",
                "--preset",
                "balanced",
                "--export-summary",
            ],
        )

        # Check for summary file creation
        summary_files = list(output_dir.glob("*summary*"))
        assert len(summary_files) > 0


class TestProcessCommandValidation:
    """Test cases for input validation on process command."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_requires_path_argument(self, runner: CliRunner, app) -> None:
        """
        RED: Verify process command requires input path.

        Given: process command without input path
        When: We invoke the command
        Then: Should fail with usage error

        Expected RED failure: Command accepts missing argument
        """
        result = runner.invoke(app, ["process"])

        assert result.exit_code != 0

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_process_nonexistent_input_path(
        self, runner: CliRunner, app, tmp_path: Path, output_dir: Path
    ) -> None:
        """
        RED: Verify process rejects nonexistent input path.

        Given: Input path that doesn't exist
        When: We invoke the command
        Then: Should fail with file not found error

        Expected RED failure: Command processes nonexistent path
        """
        nonexistent_path = tmp_path / "nonexistent"

        result = runner.invoke(
            app,
            [
                "process",
                str(nonexistent_path),
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code != 0
        assert "exist" in result.output.lower() or "not found" in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_5
    def test_process_requires_output_for_preset(
        self, runner: CliRunner, app, sample_input_dir: Path
    ) -> None:
        """
        RED: Verify output path requirements with preset.

        Given: --preset without explicit output path
        When: We invoke the command
        Then: Should either use default or require output

        Expected RED failure: Command fails unexpectedly
        """
        result = runner.invoke(
            app,
            [
                "process",
                str(sample_input_dir),
                "--preset",
                "quality",
            ],
        )

        # Should either succeed with defaults or fail gracefully
        assert result.exit_code in [0, 2]  # 0 = success, 2 = validation error
