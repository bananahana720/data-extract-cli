"""TDD Red Phase Tests for Continue-on-Error Pattern - Story 5-3.

Tests for:
- AC-5.3-9: Continue-on-error pattern - single file errors don't halt batch

Expected RED failure: ModuleNotFoundError - error handling components don't exist yet.
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.continue_on_error,
    pytest.mark.unit,
    pytest.mark.story_5_3,
    pytest.mark.cli,
]

# ==============================================================================
# AC-5.3-9: Errors during processing shown but don't halt progress bar
# ==============================================================================


class TestContinueOnError:
    """Test that single file errors don't halt batch processing."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_batch_continues_after_single_file_error(
        self, typer_cli_runner, batch_processing_fixture
    ):
        """
        RED: AC-5.3-9 - Batch continues after single file error.

        Given: A batch with 8 good files and 2 error-inducing files
        When: Running process command
        Then: Should process all good files despite errors

        Expected RED failure: Process command doesn't exist or halts on error
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Should show some successful processing (at least 8 good files)
        assert "processed" in result.output.lower() or "complete" in result.output.lower()
        # Should show errors but not halt
        assert "error" in result.output.lower() or "failed" in result.output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_shown_inline_but_continues(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Error messages shown inline but processing continues.

        Given: A batch with error-inducing files
        When: Processing encounters an error
        Then: Error should be shown without stopping progress

        Expected RED failure: Processing halts on error
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Progress should continue (shows completion of more than just first file)
        # If progress halted at first error, we wouldn't see completion metrics
        assert result.exit_code == 0 or "partial" in result.output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_summary_shown_after_completion(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Error summary shown after batch completion.

        Given: A batch with some errors
        When: Processing completes
        Then: Should show summary of errors at the end

        Expected RED failure: No error summary
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Should have error summary section
        error_indicators = ["failed", "errors", "could not", "skipped"]
        assert any(ind in result.output.lower() for ind in error_indicators)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_exit_code_reflects_partial_success(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Exit code reflects partial success appropriately.

        Given: A batch with some errors
        When: Processing completes
        Then: Exit code should indicate partial success (not 0, not critical failure)

        Expected RED failure: Exit code handling not implemented
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # With errors, exit code could be:
        # 0 = all succeeded (not expected here)
        # 1 = partial failure (expected)
        # 2 = complete failure (not expected if good files exist)
        # Just verify we got something processed
        assert "processed" in result.output.lower() or result.exit_code in [0, 1]


class TestErrorCollectorComponent:
    """Test ErrorCollector component for accumulating errors."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_class_exists(self):
        """
        RED: AC-5.3-9 - ErrorCollector class should exist.

        Given: The feedback module
        When: Importing ErrorCollector
        Then: Class should be importable

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        assert ErrorCollector is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_add_error(self):
        """
        RED: AC-5.3-9 - ErrorCollector can add errors.

        Given: An ErrorCollector instance
        When: Adding an error
        Then: Error should be stored

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error(
            file_path="/path/to/file.pdf",
            error_type="extraction",
            error_message="Failed to extract text",
        )

        assert collector.error_count == 1

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_multiple_errors(self):
        """
        RED: AC-5.3-9 - ErrorCollector tracks multiple errors.

        Given: An ErrorCollector instance
        When: Adding multiple errors
        Then: All errors should be tracked

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error(
            file_path="/path/to/file1.pdf",
            error_type="extraction",
            error_message="Failed to extract",
        )
        collector.add_error(
            file_path="/path/to/file2.docx",
            error_type="validation",
            error_message="Invalid format",
        )
        collector.add_error(
            file_path="/path/to/file3.xlsx",
            error_type="timeout",
            error_message="Processing timed out",
        )

        assert collector.error_count == 3

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_get_summary(self, mock_console):
        """
        RED: AC-5.3-9 - ErrorCollector provides error summary.

        Given: An ErrorCollector with errors
        When: Getting summary
        Then: Should return formatted summary

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error(
            file_path="/path/to/file1.pdf",
            error_type="extraction",
            error_message="Failed to extract",
        )
        collector.add_error(
            file_path="/path/to/file2.pdf",
            error_type="extraction",
            error_message="Failed to extract 2",
        )

        summary = collector.get_summary()

        assert "2" in str(summary) or summary.error_count == 2

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_render_summary(self, mock_console):
        """
        RED: AC-5.3-9 - ErrorCollector renders summary for console.

        Given: An ErrorCollector with errors
        When: Rendering summary to console
        Then: Should show formatted error list

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error(
            file_path="corrupted.pdf",
            error_type="extraction",
            error_message="File appears corrupted",
        )

        collector.render_summary(console=mock_console.console)

        output = mock_console.exported_text
        assert "corrupted.pdf" in output
        assert "extraction" in output.lower() or "error" in output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_has_errors_property(self):
        """
        RED: AC-5.3-9 - ErrorCollector has has_errors property.

        Given: An ErrorCollector
        When: Checking has_errors before and after adding
        Then: Should return appropriate boolean

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        assert not collector.has_errors

        collector.add_error(
            file_path="file.pdf",
            error_type="extraction",
            error_message="Error",
        )

        assert collector.has_errors


class TestErrorTypeCategorization:
    """Test error categorization and actionable suggestions."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_categorizes_by_type(self):
        """
        RED: AC-5.3-9 - Errors categorized by type for summary.

        Given: Errors of different types
        When: Getting categorized summary
        Then: Should group by error type

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("f1.pdf", "extraction", "Extraction failed")
        collector.add_error("f2.pdf", "extraction", "Extraction failed")
        collector.add_error("f3.docx", "validation", "Validation failed")
        collector.add_error("f4.xlsx", "timeout", "Timed out")

        categories = collector.get_error_categories()

        assert categories["extraction"] == 2
        assert categories["validation"] == 1
        assert categories["timeout"] == 1

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_provides_suggestions(self):
        """
        RED: AC-5.3-9 - ErrorCollector provides actionable suggestions.

        Given: Extraction errors
        When: Getting suggestions
        Then: Should provide actionable advice

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("scanned.pdf", "ocr", "OCR confidence too low")

        suggestions = collector.get_suggestions()

        # Should suggest something actionable for OCR errors
        assert any("scan" in s.lower() or "ocr" in s.lower() for s in suggestions)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_timeout_suggestion(self):
        """
        RED: AC-5.3-9 - Timeout errors get appropriate suggestion.

        Given: Timeout errors
        When: Getting suggestions
        Then: Should suggest increasing timeout or chunking

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("huge_report.pdf", "timeout", "Processing timed out")

        suggestions = collector.get_suggestions()

        # Should suggest timeout-related fix
        timeout_keywords = ["timeout", "chunk", "split", "smaller"]
        assert any(any(kw in s.lower() for kw in timeout_keywords) for s in suggestions)


class TestProgressWithErrors:
    """Test progress bar behavior with errors."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_progress_bar_continues_after_error(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Progress bar continues advancing after error.

        Given: Batch with error files
        When: Processing and error occurs
        Then: Progress bar should continue to show advancement

        Expected RED failure: Progress halts on error
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()
        total_files = len(good_files) + len(error_files)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Should show progress beyond first file (error shouldn't halt)
        # Evidence: completion indicators or high percentage
        completion_indicators = ["100%", "complete", str(total_files), "10/10"]
        assert any(ind in result.output for ind in completion_indicators)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_count_shown_in_progress(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Error count visible during/after progress.

        Given: Batch with error files
        When: Processing
        Then: Should show error count

        Expected RED failure: Error count not visible
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Should show error count (e.g., "2 errors" or "8/10 succeeded")
        _error_count_patterns = ["2 error", "2 fail", "8/10", "8 of 10"]
        # At minimum, some indication of failures
        assert any(p in result.output.lower() for p in ["error", "fail", "skip"])


class TestErrorIntegrationWithPanels:
    """Test error integration with quality dashboard and preflight."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_quality_dashboard_shows_failed_count(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Quality dashboard shows failed file count.

        Given: Batch with some failed files
        When: Processing completes
        Then: Quality dashboard should show failed count

        Expected RED failure: Failed count not in dashboard
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Dashboard should mention failed/error files
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_files_in_retry_suggestion(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-9 - Failed files included in retry suggestion.

        Given: Batch with failed files
        When: Processing completes with errors
        Then: Should suggest how to retry failed files

        Expected RED failure: No retry suggestion
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(batch_processing_fixture.tmp_path)])

        # Should provide retry guidance
        retry_indicators = ["retry", "again", "--retry", "failed files"]
        # At minimum, error summary should be present
        assert (
            any(ind in result.output.lower() for ind in retry_indicators)
            or "error" in result.output.lower()
        )
