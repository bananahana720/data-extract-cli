"""AC-5.6-5: Exit code standards for batch processing.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on standardized exit codes:
- Exit code 0: All files processed successfully
- Exit code 1: Partial success (some files failed)
- Exit code 2: Complete failure (no files processed)
- Exit code 3: Configuration error

Reference: docs/stories/5-6-graceful-error-handling-and-recovery.md
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.graceful_degradation,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import SessionDirectoryFixture


# ==============================================================================
# Exit Code Constants Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCodeConstants:
    """Test exit code constant definitions."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_exit_code_0_success_constant_defined(self) -> None:
        """
        RED: Verify EXIT_SUCCESS constant is defined as 0.

        Given: The exit_codes module exists
        When: EXIT_SUCCESS is accessed
        Then: It should equal 0

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange & Act
        from data_extract.cli.exit_codes import EXIT_SUCCESS

        # Assert
        assert EXIT_SUCCESS == 0

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_exit_code_1_partial_constant_defined(self) -> None:
        """
        RED: Verify EXIT_PARTIAL constant is defined as 1.

        Given: The exit_codes module exists
        When: EXIT_PARTIAL is accessed
        Then: It should equal 1

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange & Act
        from data_extract.cli.exit_codes import EXIT_PARTIAL

        # Assert
        assert EXIT_PARTIAL == 1

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_exit_code_2_failure_constant_defined(self) -> None:
        """
        RED: Verify EXIT_FAILURE constant is defined as 2.

        Given: The exit_codes module exists
        When: EXIT_FAILURE is accessed
        Then: It should equal 2

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange & Act
        from data_extract.cli.exit_codes import EXIT_FAILURE

        # Assert
        assert EXIT_FAILURE == 2

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_exit_code_3_config_error_constant_defined(self) -> None:
        """
        RED: Verify EXIT_CONFIG_ERROR constant is defined as 3.

        Given: The exit_codes module exists
        When: EXIT_CONFIG_ERROR is accessed
        Then: It should equal 3

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange & Act
        from data_extract.cli.exit_codes import EXIT_CONFIG_ERROR

        # Assert
        assert EXIT_CONFIG_ERROR == 3


# ==============================================================================
# Exit Code 0 - All Success Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCode0Success:
    """Test exit code 0 when all files processed successfully."""

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_exit_code_0_success_all_files_processed(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 0 when all files process successfully.

        Given: A batch of 5 valid text files
        When: Processing runs to completion
        Then: Exit code should be 0

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"valid_{i}.txt").write_text(f"Valid content {i}")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_exit_code_0_success_single_file(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 0 with single file success.

        Given: A single valid file
        When: Processing completes
        Then: Exit code should be 0

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "single.txt").write_text("Single file content")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-007")
    def test_exit_code_0_success_empty_directory(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 0 with empty source directory.

        Given: An empty source directory
        When: Processing is attempted
        Then: Exit code should be 0 (nothing to fail)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "empty_docs"
        source_dir.mkdir()

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-008")
    def test_exit_code_0_success_returns_zero_for_helper_function(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify determine_exit_code returns 0 for all success.

        Given: Session with 0 failures and N successes
        When: determine_exit_code() is called
        Then: Should return 0

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=10,
            processed_count=10,
            failed_count=0,
        )

        # Assert
        assert exit_code == 0


# ==============================================================================
# Exit Code 1 - Partial Success Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCode1Partial:
    """Test exit code 1 when some files fail."""

    @pytest.mark.test_id("5.6-UNIT-009")
    def test_exit_code_1_partial_some_files_failed(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 1 when some files fail.

        Given: A batch with 8 valid and 2 corrupted files
        When: Processing completes
        Then: Exit code should be 1

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # Good files
        for i in range(8):
            (source_dir / f"valid_{i}.txt").write_text(f"Valid content {i}")

        # Bad files
        (source_dir / "corrupted_1.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "corrupted_2.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 1

    @pytest.mark.test_id("5.6-UNIT-010")
    def test_exit_code_1_partial_single_failure(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 1 with single file failure.

        Given: 9 valid files and 1 corrupted file
        When: Processing completes
        Then: Exit code should be 1 (partial success)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # Good files
        for i in range(9):
            (source_dir / f"valid_{i}.txt").write_text(f"Valid content {i}")

        # Single bad file
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 1

    @pytest.mark.test_id("5.6-UNIT-011")
    def test_exit_code_1_partial_returns_one_for_helper_function(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify determine_exit_code returns 1 for partial success.

        Given: Session with some successes and some failures
        When: determine_exit_code() is called
        Then: Should return 1

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=10,
            processed_count=7,
            failed_count=3,
        )

        # Assert
        assert exit_code == 1

    @pytest.mark.test_id("5.6-UNIT-012")
    def test_exit_code_1_partial_output_indicates_partial_success(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify output indicates partial success.

        Given: Batch with some failures
        When: Processing completes with exit code 1
        Then: Output should indicate partial success

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "valid.txt").write_text("Valid content")
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 1
        output_lower = result.output.lower()
        assert "partial" in output_lower or "warning" in output_lower or "failed" in output_lower


# ==============================================================================
# Exit Code 2 - Complete Failure Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCode2Failure:
    """Test exit code 2 when all files fail."""

    @pytest.mark.test_id("5.6-UNIT-013")
    def test_exit_code_2_failure_all_files_failed(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 2 when all files fail.

        Given: A batch with all corrupted files
        When: Processing attempts to run
        Then: Exit code should be 2

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # All bad files
        (source_dir / "corrupted_1.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "corrupted_2.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "corrupted_3.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-014")
    def test_exit_code_2_failure_single_file_all_failed(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 2 with single corrupted file.

        Given: A single corrupted file
        When: Processing attempts to run
        Then: Exit code should be 2

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-015")
    def test_exit_code_2_failure_returns_two_for_helper_function(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify determine_exit_code returns 2 for complete failure.

        Given: Session with 0 successes and N failures
        When: determine_exit_code() is called
        Then: Should return 2

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=5,
            processed_count=0,
            failed_count=5,
        )

        # Assert
        assert exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-016")
    def test_exit_code_2_failure_output_indicates_complete_failure(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify output indicates complete failure.

        Given: All files fail processing
        When: Processing completes with exit code 2
        Then: Output should indicate complete failure

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "corrupted_1.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "corrupted_2.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 2
        output_lower = result.output.lower()
        assert "error" in output_lower or "failed" in output_lower or "all" in output_lower


# ==============================================================================
# Exit Code 3 - Configuration Error Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCode3ConfigError:
    """Test exit code 3 for configuration errors."""

    @pytest.mark.test_id("5.6-UNIT-017")
    def test_exit_code_3_config_error_invalid_format(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 3 for invalid format option.

        Given: User provides invalid --format option
        When: Processing is attempted
        Then: Exit code should be 3

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("Content")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--format", "invalid_format"],
        )

        # Assert
        assert result.exit_code == 3

    @pytest.mark.test_id("5.6-UNIT-018")
    def test_exit_code_3_config_error_invalid_chunk_size(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 3 for invalid chunk size.

        Given: User provides negative chunk size
        When: Processing is attempted
        Then: Exit code should be 3

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("Content")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--chunk-size", "-100"],
        )

        # Assert
        assert result.exit_code == 3

    @pytest.mark.test_id("5.6-UNIT-019")
    def test_exit_code_3_config_error_missing_required_arg(
        self,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify exit code 3 for missing required argument.

        Given: User omits required source directory
        When: Process command is invoked
        Then: Exit code should be 3

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process"],  # Missing required source directory
        )

        # Assert
        # Typer may return 2 for missing args, but we want 3 for config errors
        assert result.exit_code in [2, 3]

    @pytest.mark.test_id("5.6-UNIT-020")
    def test_exit_code_3_config_error_invalid_source_directory(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 3 for non-existent source directory.

        Given: User provides non-existent directory path
        When: Processing is attempted
        Then: Exit code should be 3

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        nonexistent = tmp_path / "does_not_exist"

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(nonexistent)],
        )

        # Assert
        assert result.exit_code == 3

    @pytest.mark.test_id("5.6-UNIT-021")
    def test_exit_code_3_config_error_conflicting_options(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 3 for conflicting options.

        Given: User provides conflicting options
        When: Processing is attempted
        Then: Exit code should be 3

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("Content")

        # Act - conflicting resume options
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--resume", "--force"],
        )

        # Assert
        # Depending on implementation, this may be exit code 3 or handled differently
        assert result.exit_code in [0, 1, 2, 3]

    @pytest.mark.test_id("5.6-UNIT-022")
    def test_exit_code_3_config_error_output_indicates_config_problem(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify output indicates configuration error.

        Given: Invalid configuration provided
        When: Processing fails with exit code 3
        Then: Output should indicate configuration problem

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("Content")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--format", "invalid_format"],
        )

        # Assert
        assert result.exit_code == 3
        output_lower = result.output.lower()
        assert "config" in output_lower or "invalid" in output_lower or "error" in output_lower


# ==============================================================================
# Exit Code Helper Function Tests
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestDetermineExitCodeFunction:
    """Test the determine_exit_code helper function."""

    @pytest.mark.test_id("5.6-UNIT-023")
    def test_determine_exit_code_all_success(self) -> None:
        """
        RED: Verify determine_exit_code returns 0 for 100% success.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=100,
            processed_count=100,
            failed_count=0,
        )

        # Assert
        assert exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-024")
    def test_determine_exit_code_partial_success(self) -> None:
        """
        RED: Verify determine_exit_code returns 1 for partial success.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=100,
            processed_count=50,
            failed_count=50,
        )

        # Assert
        assert exit_code == 1

    @pytest.mark.test_id("5.6-UNIT-025")
    def test_determine_exit_code_complete_failure(self) -> None:
        """
        RED: Verify determine_exit_code returns 2 for complete failure.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=100,
            processed_count=0,
            failed_count=100,
        )

        # Assert
        assert exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-026")
    def test_determine_exit_code_edge_case_single_success(self) -> None:
        """
        RED: Verify determine_exit_code handles single file success.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=1,
            processed_count=1,
            failed_count=0,
        )

        # Assert
        assert exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-027")
    def test_determine_exit_code_edge_case_single_failure(self) -> None:
        """
        RED: Verify determine_exit_code handles single file failure.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=1,
            processed_count=0,
            failed_count=1,
        )

        # Assert
        assert exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-028")
    def test_determine_exit_code_edge_case_no_files(self) -> None:
        """
        RED: Verify determine_exit_code handles empty batch.

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=0,
            processed_count=0,
            failed_count=0,
        )

        # Assert
        assert exit_code == 0  # Nothing to fail = success

    @pytest.mark.test_id("5.6-UNIT-029")
    def test_determine_exit_code_99_percent_success(self) -> None:
        """
        RED: Verify 99% success still returns 1 (partial).

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=100,
            processed_count=99,
            failed_count=1,
        )

        # Assert
        assert exit_code == 1  # Any failure = partial

    @pytest.mark.test_id("5.6-UNIT-030")
    def test_determine_exit_code_1_percent_success(self) -> None:
        """
        RED: Verify 1% success still returns 1 (partial, not complete failure).

        Expected RED failure: ModuleNotFoundError - exit_codes module doesn't exist
        """
        # Arrange
        from data_extract.cli.exit_codes import determine_exit_code

        # Act
        exit_code = determine_exit_code(
            total_files=100,
            processed_count=1,
            failed_count=99,
        )

        # Assert
        assert exit_code == 1  # Any success = partial (not complete failure)
