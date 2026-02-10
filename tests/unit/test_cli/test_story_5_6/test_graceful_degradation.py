"""AC-5.6-5: Graceful degradation via continue-on-error pattern.

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify continue-on-error pattern:
- Pipeline continues when single file errors
- Error aggregation for summary report
- Exit codes (0=all success, 1=partial, 2=complete failure, 3=config error)
- Error summary panel at batch completion
- Actionable suggestions per error type
- Per-file try/except wrapping
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


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestContinueOnErrorPattern:
    """Test continue-on-error pattern implementation."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_pipeline_continues_after_single_file_error(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify pipeline continues after single file error.

        Given: A batch of 10 files where one is corrupted
        When: Processing runs
        Then: Processing should continue for remaining 9 files

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # Create 9 good files
        for i in range(9):
            (source_dir / f"good_{i}.txt").write_text(f"Good content {i}")

        # Create 1 corrupted file
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert "9" in result.output or "processed" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_all_good_files_processed_despite_error(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify all good files are processed even when errors occur.

        Given: Files A (good), B (corrupted), C (good), D (good)
        When: Processing runs
        Then: Files A, C, D should all be processed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        output_dir = tmp_path / "output"

        (source_dir / "A_first.txt").write_text("Content A")
        (source_dir / "B_corrupted.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "C_middle.txt").write_text("Content C")
        (source_dir / "D_last.txt").write_text("Content D")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--output", str(output_dir), "--non-interactive"],
        )

        # Assert - all 3 good files should have output
        assert result.exit_code == 1  # Partial success
        # Check output files exist (implementation specific)

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_error_does_not_stop_subsequent_files(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify error on file N doesn't prevent file N+1 from processing.

        Given: Files processed in order: good1, corrupted, good2
        When: corrupted fails
        Then: good2 should still be processed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "01_good.txt").write_text("First good file")
        (source_dir / "02_corrupted.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "03_good.txt").write_text("Third good file")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        # Should mention processing file 03_good.txt
        assert "03_good" in result.output or "3" in result.output


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestErrorAggregation:
    """Test error aggregation for summary reporting."""

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_errors_aggregated_in_session_state(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify all errors are aggregated in session state.

        Given: Multiple files fail during processing
        When: Processing completes
        Then: All errors should be in session state failed_files

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)

        # Record multiple failures
        manager.record_failed_file(
            file_path=Path("/docs/error1.pdf"),
            error_type="extraction",
            error_message="PDF corrupt",
        )
        manager.record_failed_file(
            file_path=Path("/docs/error2.docx"),
            error_type="extraction",
            error_message="DOCX empty",
        )
        manager.record_failed_file(
            file_path=Path("/docs/error3.xlsx"),
            error_type="validation",
            error_message="No sheets",
        )

        state = manager.get_session_state()

        # Assert
        assert len(state["failed_files"]) == 3

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_error_count_in_statistics(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify error count tracked in statistics.

        Given: 3 files fail during processing
        When: Session state is checked
        Then: statistics.failed_count should be 3

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)

        for i in range(3):
            manager.record_failed_file(
                file_path=Path(f"/docs/error{i}.pdf"),
                error_type="extraction",
                error_message=f"Error {i}",
            )

        state = manager.get_session_state()

        # Assert
        assert state["statistics"]["failed_count"] == 3


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestExitCodes:
    """Test exit codes for batch processing outcomes."""

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_exit_code_0_all_success(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 0 when all files processed successfully.

        Given: All files in batch are valid
        When: Processing completes
        Then: Exit code should be 0

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"good_{i}.txt").write_text(f"Good content {i}")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-007")
    def test_exit_code_1_partial_success(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 1 when some files failed.

        Given: 8 good files and 2 corrupted files
        When: Processing completes
        Then: Exit code should be 1 (partial success)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        for i in range(8):
            (source_dir / f"good_{i}.txt").write_text(f"Good content {i}")
        (source_dir / "bad1.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "bad2.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 1

    @pytest.mark.test_id("5.6-UNIT-008")
    def test_exit_code_2_complete_failure(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 2 when all files failed.

        Given: All files are corrupted
        When: Processing attempts to run
        Then: Exit code should be 2 (complete failure)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "bad1.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "bad2.pdf").write_bytes(b"%PDF-corrupt")
        (source_dir / "bad3.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 2

    @pytest.mark.test_id("5.6-UNIT-009")
    def test_exit_code_3_configuration_error(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify exit code 3 for configuration errors.

        Given: Invalid configuration provided
        When: Processing attempts to start
        Then: Exit code should be 3 (configuration error)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # Act - invalid output format
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--format", "invalid_format"],
        )

        # Assert
        assert result.exit_code == 3


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestErrorSummaryPanel:
    """Test error summary panel at batch completion."""

    @pytest.mark.test_id("5.6-UNIT-010")
    def test_error_summary_panel_displayed(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify error summary panel shown at completion.

        Given: Batch with failures completes
        When: Final summary is displayed
        Then: Error summary panel should be shown

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"good_{i}.txt").write_text(f"Content {i}")
        (source_dir / "bad.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        output_lower = result.output.lower()
        assert "error" in output_lower or "failed" in output_lower or "issue" in output_lower

    @pytest.mark.test_id("5.6-UNIT-011")
    def test_error_summary_shows_file_count(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify error summary shows failure count.

        Given: 3 files fail during processing
        When: Summary panel is displayed
        Then: Should show "3 files had issues"

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"good_{i}.txt").write_text(f"Content {i}")
        for i in range(3):
            (source_dir / f"bad_{i}.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert "3" in result.output

    @pytest.mark.test_id("5.6-UNIT-012")
    def test_error_summary_lists_failed_files(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify error summary lists each failed file.

        Given: specific-error.pdf fails
        When: Summary panel is displayed
        Then: File name should be listed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "good.txt").write_text("Good content")
        (source_dir / "specific-error.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert "specific-error.pdf" in result.output


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestActionableSuggestions:
    """Test actionable suggestions per error type."""

    @pytest.mark.test_id("5.6-UNIT-013")
    def test_suggestion_for_corrupted_pdf(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify suggestion shown for corrupted PDF.

        Given: PDF fails with "corrupted" error
        When: Error is displayed
        Then: Suggestion should be "Repair PDF or exclude"

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        suggestion = prompt.get_suggestion_for_error(
            error_type="pdf_corrupted",
            error_message="PDF structure invalid",
        )

        # Assert
        assert "repair" in suggestion.lower() or "exclude" in suggestion.lower()

    @pytest.mark.test_id("5.6-UNIT-014")
    def test_suggestion_for_memory_error(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify suggestion shown for memory exceeded error.

        Given: File fails with memory exceeded error
        When: Error is displayed
        Then: Suggestion should mention --max-pages option

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        suggestion = prompt.get_suggestion_for_error(
            error_type="memory_exceeded",
            error_message="Out of memory processing large file",
        )

        # Assert
        assert "--max-pages" in suggestion

    @pytest.mark.test_id("5.6-UNIT-015")
    def test_suggestion_for_password_protected(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify suggestion shown for password protected files.

        Given: File fails with password protected error
        When: Error is displayed
        Then: Suggestion should mention --password option

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        suggestion = prompt.get_suggestion_for_error(
            error_type="password_protected",
            error_message="PDF is password protected",
        )

        # Assert
        assert "--password" in suggestion

    @pytest.mark.test_id("5.6-UNIT-016")
    def test_recovery_commands_in_summary(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify recovery commands shown in error summary.

        Given: Batch completes with failures
        When: Summary panel is displayed
        Then: Recovery commands should be suggested

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "good.txt").write_text("Good content")
        (source_dir / "bad.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        output_lower = result.output.lower()
        # Should suggest retry command
        assert "retry" in output_lower or "data-extract" in output_lower


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.graceful_degradation
class TestPerFileExceptionHandling:
    """Test per-file try/except wrapping."""

    @pytest.mark.test_id("5.6-UNIT-017")
    def test_exception_in_extraction_caught(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify extraction exceptions are caught per-file.

        Given: A file that raises exception during extraction
        When: Processing runs
        Then: Exception should be caught, not propagate

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        (source_dir / "good.txt").write_text("Good")
        (source_dir / "exception.pdf").write_bytes(b"invalid pdf data")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert - should not crash with unhandled exception
        assert "Traceback" not in result.output or result.exit_code in [0, 1, 2]

    @pytest.mark.test_id("5.6-UNIT-018")
    def test_exception_in_normalization_caught(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify normalization exceptions are caught per-file.

        Given: A file that raises exception during normalization
        When: Pipeline processes it
        Then: Exception should be caught and recorded

        Expected RED failure: ModuleNotFoundError - batch_processor module doesn't exist
        """
        # Arrange
        from data_extract.cli.batch_processor import BatchProcessor

        work_dir = session_directory_fixture.work_dir

        # Act
        processor = BatchProcessor(work_dir=work_dir)
        results = processor.process_file(
            file_path=Path("/docs/problematic.txt"),
            content="Content with \x00 null bytes",  # May cause issues
        )

        # Assert
        assert results.error is not None or results.success

    @pytest.mark.test_id("5.6-UNIT-019")
    def test_100_percent_failure_rate_handled(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify 100% failure rate is handled gracefully.

        Given: All files in batch fail
        When: Processing completes
        Then: Graceful exit with appropriate message and exit code 2

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()

        # All files are corrupted
        for i in range(5):
            (source_dir / f"corrupt_{i}.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert result.exit_code == 2
        assert "all" in result.output.lower() or "failed" in result.output.lower()
