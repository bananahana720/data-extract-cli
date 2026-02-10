"""TDD Red Phase Tests for Feedback Components - Story 5-3.

Consolidated tests for feedback infrastructure:
- AC-5.3-5: NO_COLOR environment variable support
- AC-5.3-8: Quiet mode (-q) and verbose levels (-v, -vv, -vvv)
- AC-5.3-9: Continue-on-error pattern with ErrorCollector

Expected RED failure: ModuleNotFoundError - feedback components don't exist yet.
"""

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.no_color,
    pytest.mark.unit,
    pytest.mark.continue_on_error,
    pytest.mark.verbosity,
    pytest.mark.story_5_3,
    pytest.mark.cli,
]

# ==============================================================================
# Verbosity Level Tests (AC-5.3-8)
# ==============================================================================


class TestVerbosityLevels:
    """Test VerbosityController handles all verbosity levels correctly."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_quiet_mode_level_zero(self):
        """
        RED: AC-5.3-8 - Quiet mode is level 0.

        Given: VerbosityController
        When: Creating with level=0
        Then: Should represent quiet mode (-q flag)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=0)

        assert controller.level == 0
        assert controller.is_quiet
        assert not controller.is_verbose
        assert not controller.is_debug
        assert not controller.is_trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_normal_mode_level_one(self):
        """
        RED: AC-5.3-8 - Normal mode is level 1 (default).

        Given: VerbosityController
        When: Creating with level=1 (default)
        Then: Should represent normal mode (no flags)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=1)

        assert controller.level == 1
        assert not controller.is_quiet
        assert not controller.is_verbose
        assert not controller.is_debug
        assert not controller.is_trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_verbose_mode_level_two(self):
        """
        RED: AC-5.3-8 - Verbose mode is level 2 (-v flag).

        Given: VerbosityController
        When: Creating with level=2
        Then: Should represent verbose mode

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=2)

        assert controller.level == 2
        assert controller.is_verbose
        assert not controller.is_quiet
        assert not controller.is_debug
        assert not controller.is_trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_debug_mode_level_three(self):
        """
        RED: AC-5.3-8 - Debug mode is level 3 (-vv flag).

        Given: VerbosityController
        When: Creating with level=3
        Then: Should represent debug mode

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=3)

        assert controller.level == 3
        assert controller.is_debug
        assert controller.is_verbose  # Debug includes verbose
        assert not controller.is_quiet
        assert not controller.is_trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_trace_mode_level_four(self):
        """
        RED: AC-5.3-8 - Trace mode is level 4 (-vvv flag).

        Given: VerbosityController
        When: Creating with level=4
        Then: Should represent trace mode (maximum verbosity)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=4)

        assert controller.level == 4
        assert controller.is_trace
        assert controller.is_debug  # Trace includes debug
        assert controller.is_verbose  # Trace includes verbose
        assert not controller.is_quiet


class TestVerbosityFiltering:
    """Test VerbosityController message filtering logic."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_mode_suppresses_normal_messages(self, mock_console):
        """
        RED: AC-5.3-8 - Quiet mode suppresses normal messages.

        Given: VerbosityController at level 0 (quiet)
        When: Logging a normal message
        Then: Message should not be output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=0, console=mock_console.console)

        controller.log("Normal message", level="normal")
        controller.log("Info message", level="info")

        assert "Normal message" not in mock_console.exported_text
        assert "Info message" not in mock_console.exported_text

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_mode_shows_errors(self, mock_console):
        """
        RED: AC-5.3-8 - Quiet mode still shows errors.

        Given: VerbosityController at level 0 (quiet)
        When: Logging an error message
        Then: Error should still be output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=0, console=mock_console.console)

        controller.log("Critical error occurred", level="error")

        assert "error" in mock_console.exported_text.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_normal_mode_shows_summary_not_debug(self, mock_console):
        """
        RED: AC-5.3-8 - Normal mode shows summary but not debug.

        Given: VerbosityController at level 1 (normal)
        When: Logging messages at various levels
        Then: Only normal and below should be output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=1, console=mock_console.console)

        controller.log("Normal message", level="normal")
        controller.log("Debug message", level="debug")
        controller.log("Trace message", level="trace")

        output = mock_console.exported_text
        assert "Normal message" in output
        assert "Debug message" not in output
        assert "Trace message" not in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbose_mode_shows_per_file_info(self, mock_console):
        """
        RED: AC-5.3-8 - Verbose mode shows per-file information.

        Given: VerbosityController at level 2 (verbose)
        When: Logging verbose-level messages
        Then: Messages should be output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=2, console=mock_console.console)

        controller.log("Processing file.pdf", level="verbose")
        controller.log("Extracted 1000 words", level="verbose")

        output = mock_console.exported_text
        assert "Processing file.pdf" in output
        assert "1000 words" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_debug_mode_shows_timing_info(self, mock_console):
        """
        RED: AC-5.3-8 - Debug mode shows timing information.

        Given: VerbosityController at level 3 (debug)
        When: Logging debug-level messages with timing
        Then: Timing info should be output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=3, console=mock_console.console)

        controller.log("Operation took 145ms", level="debug")
        controller.log("DEBUG: TF-IDF vectorization complete", level="debug")

        output = mock_console.exported_text
        assert "145ms" in output or "DEBUG" in output


class TestVerbosityDefaultBehavior:
    """Test VerbosityController default and factory behavior."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_default_verbosity_is_normal(self):
        """
        RED: AC-5.3-8 - Default verbosity is normal (level 1).

        Given: VerbosityController created without level
        When: Checking default level
        Then: Should be level 1 (normal)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController()

        assert controller.level == 1

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_from_flag_count(self):
        """
        RED: AC-5.3-8 - Verbosity can be created from flag count.

        Given: VerbosityController factory method
        When: Creating from verbose flag count
        Then: Should map correctly (-v=2, -vv=3, -vvv=4)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        # Factory method for CLI integration
        from_zero = VerbosityController.from_verbose_count(0)
        from_one = VerbosityController.from_verbose_count(1)
        from_two = VerbosityController.from_verbose_count(2)
        from_three = VerbosityController.from_verbose_count(3)

        assert from_zero.level == 1  # No -v = normal
        assert from_one.level == 2  # -v = verbose
        assert from_two.level == 3  # -vv = debug
        assert from_three.level == 4  # -vvv = trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_from_quiet_flag(self):
        """
        RED: AC-5.3-8 - Verbosity can be created from quiet flag.

        Given: VerbosityController factory method
        When: Creating with quiet=True
        Then: Should be level 0

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController.from_flags(quiet=True)

        assert controller.level == 0
        assert controller.is_quiet


# ==============================================================================
# Error Collector Tests (AC-5.3-9)
# ==============================================================================


class TestErrorCollectorBasics:
    """Test ErrorCollector basic functionality."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_exists(self):
        """
        RED: AC-5.3-9 - ErrorCollector class exists.

        Given: The feedback module
        When: Importing ErrorCollector
        Then: Should be importable

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        assert ErrorCollector is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_starts_empty(self):
        """
        RED: AC-5.3-9 - ErrorCollector starts with no errors.

        Given: New ErrorCollector
        When: Checking initial state
        Then: Should have 0 errors

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        assert collector.error_count == 0
        assert not collector.has_errors
        assert len(collector.errors) == 0

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_accumulates_errors(self):
        """
        RED: AC-5.3-9 - ErrorCollector accumulates multiple errors.

        Given: ErrorCollector
        When: Adding multiple errors
        Then: All errors should be tracked

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("file1.pdf", "extraction", "Failed to extract")
        collector.add_error("file2.docx", "validation", "Invalid format")
        collector.add_error("file3.xlsx", "timeout", "Timed out")

        assert collector.error_count == 3
        assert collector.has_errors


class TestErrorCollectorCategories:
    """Test ErrorCollector categorization features."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_groups_by_type(self):
        """
        RED: AC-5.3-9 - ErrorCollector groups errors by type.

        Given: Errors of various types
        When: Getting categorized summary
        Then: Should group by error type

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("f1.pdf", "extraction", "Error 1")
        collector.add_error("f2.pdf", "extraction", "Error 2")
        collector.add_error("f3.pdf", "extraction", "Error 3")
        collector.add_error("f4.docx", "validation", "Error 4")
        collector.add_error("f5.xlsx", "timeout", "Error 5")

        categories = collector.get_error_categories()

        assert categories["extraction"] == 3
        assert categories["validation"] == 1
        assert categories["timeout"] == 1

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_tracks_file_paths(self):
        """
        RED: AC-5.3-9 - ErrorCollector tracks file paths.

        Given: Errors with file paths
        When: Getting error list
        Then: Should include file paths

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("/path/to/document.pdf", "extraction", "Cannot read")

        errors = collector.errors
        assert len(errors) == 1
        assert errors[0].file_path == "/path/to/document.pdf"


class TestErrorCollectorSuggestions:
    """Test ErrorCollector actionable suggestions."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_provides_ocr_suggestion(self):
        """
        RED: AC-5.3-9 - OCR errors get appropriate suggestions.

        Given: OCR-related errors
        When: Getting suggestions
        Then: Should suggest OCR remediation

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("scanned.pdf", "ocr", "Low OCR confidence")

        suggestions = collector.get_suggestions()

        ocr_keywords = ["ocr", "scan", "image", "quality"]
        assert any(any(kw in s.lower() for kw in ocr_keywords) for s in suggestions)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_provides_timeout_suggestion(self):
        """
        RED: AC-5.3-9 - Timeout errors get appropriate suggestions.

        Given: Timeout errors
        When: Getting suggestions
        Then: Should suggest timeout remediation

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("huge.pdf", "timeout", "Processing timed out")

        suggestions = collector.get_suggestions()

        timeout_keywords = ["timeout", "chunk", "split", "smaller", "increase"]
        assert any(any(kw in s.lower() for kw in timeout_keywords) for s in suggestions)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_provides_extraction_suggestion(self):
        """
        RED: AC-5.3-9 - Extraction errors get appropriate suggestions.

        Given: Extraction errors
        When: Getting suggestions
        Then: Should suggest extraction remediation

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("corrupted.pdf", "extraction", "Cannot read PDF")

        suggestions = collector.get_suggestions()

        extraction_keywords = ["extract", "corrupt", "repair", "convert", "format"]
        assert any(any(kw in s.lower() for kw in extraction_keywords) for s in suggestions)


class TestErrorCollectorRendering:
    """Test ErrorCollector console rendering."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_renders_summary_panel(self, mock_console):
        """
        RED: AC-5.3-9 - ErrorCollector renders summary as Rich panel.

        Given: ErrorCollector with errors
        When: Rendering summary
        Then: Should produce Rich panel output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("doc1.pdf", "extraction", "Failed")
        collector.add_error("doc2.pdf", "extraction", "Failed")

        collector.render_summary(console=mock_console.console)

        output = mock_console.exported_text
        assert "2" in output  # Error count
        assert "error" in output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_renders_file_list(self, mock_console):
        """
        RED: AC-5.3-9 - ErrorCollector shows failed file list.

        Given: ErrorCollector with errors
        When: Rendering summary
        Then: Should list failed files

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.add_error("important_document.pdf", "extraction", "Cannot read")

        collector.render_summary(console=mock_console.console)

        output = mock_console.exported_text
        assert "important_document.pdf" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.continue_on_error
    def test_error_collector_renders_nothing_when_empty(self, mock_console):
        """
        RED: AC-5.3-9 - Empty ErrorCollector renders nothing.

        Given: ErrorCollector with no errors
        When: Rendering summary
        Then: Should not produce error output

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        collector = ErrorCollector()

        collector.render_summary(console=mock_console.console)

        output = mock_console.exported_text
        # Should be empty or just have success message
        assert "error" not in output.lower() or "0 error" in output.lower()


# ==============================================================================
# NO_COLOR Support Tests (AC-5.3-5)
# ==============================================================================


class TestNoColorConsoleFactory:
    """Test console factory respects NO_COLOR environment."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_get_console_detects_no_color_env(self, env_vars_fixture):
        """
        RED: AC-5.3-5 - get_console() detects NO_COLOR environment.

        Given: NO_COLOR=1 set in environment
        When: Getting console via factory
        Then: Console should have no_color=True

        Expected RED failure: ModuleNotFoundError
        """
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.components.feedback import get_console

        console = get_console()

        assert console.no_color is True

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_get_console_allows_color_by_default(self, env_vars_fixture):
        """
        RED: AC-5.3-5 - get_console() allows colors by default.

        Given: NO_COLOR not set in environment
        When: Getting console via factory
        Then: Console should allow colors

        Expected RED failure: ModuleNotFoundError
        """
        # Ensure NO_COLOR is not set
        env_vars_fixture.set_no_color(enabled=False)

        from data_extract.cli.components.feedback import get_console

        console = get_console()

        # When NO_COLOR not set, no_color should be False
        assert console.no_color is False

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_get_console_is_singleton(self, env_vars_fixture):
        """
        RED: AC-5.3-5 - get_console() returns same instance.

        Given: Multiple calls to get_console
        When: Comparing returned instances
        Then: Should be the same console

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import get_console, reset_console

        # Reset to ensure clean state
        reset_console()

        console1 = get_console()
        console2 = get_console()

        assert console1 is console2


class TestFeedbackModuleExports:
    """Test feedback module exports all required components."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    def test_feedback_module_exports_verbosity_controller(self):
        """
        RED: Feedback module exports VerbosityController.

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        assert VerbosityController is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    def test_feedback_module_exports_error_collector(self):
        """
        RED: Feedback module exports ErrorCollector.

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import ErrorCollector

        assert ErrorCollector is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    def test_feedback_module_exports_get_console(self):
        """
        RED: Feedback module exports get_console factory.

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import get_console

        assert callable(get_console)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    def test_feedback_module_exports_reset_console(self):
        """
        RED: Feedback module exports reset_console for testing.

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import reset_console

        assert callable(reset_console)
