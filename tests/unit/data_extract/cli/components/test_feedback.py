"""Unit tests for CLI feedback components."""

import os
from unittest.mock import patch

import pytest
from rich.console import Console
from rich.text import Text

from data_extract.cli.components.feedback import (
    ErrorCollector,
    ErrorInfo,
    VerbosityController,
    VerbosityLevel,
    get_console,
    reset_console,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestVerbosityLevel:
    """Tests for VerbosityLevel enum."""

    def test_verbosity_levels(self):
        """Test VerbosityLevel enum values."""
        assert VerbosityLevel.QUIET == 0
        assert VerbosityLevel.NORMAL == 1
        assert VerbosityLevel.VERBOSE == 2
        assert VerbosityLevel.DEBUG == 3
        assert VerbosityLevel.TRACE == 4

    def test_verbosity_ordering(self):
        """Test that verbosity levels are properly ordered."""
        assert VerbosityLevel.QUIET < VerbosityLevel.NORMAL
        assert VerbosityLevel.NORMAL < VerbosityLevel.VERBOSE
        assert VerbosityLevel.VERBOSE < VerbosityLevel.DEBUG
        assert VerbosityLevel.DEBUG < VerbosityLevel.TRACE


class TestVerbosityController:
    """Tests for VerbosityController class."""

    def test_initialization_default(self):
        """Test VerbosityController initialization with defaults."""
        controller = VerbosityController()
        assert controller.level == VerbosityLevel.NORMAL
        assert not controller.is_quiet
        assert not controller.is_verbose
        assert not controller.is_debug
        assert not controller.is_trace

    def test_initialization_with_level(self):
        """Test VerbosityController initialization with specific level."""
        controller = VerbosityController(level=VerbosityLevel.VERBOSE)
        assert controller.level == VerbosityLevel.VERBOSE
        assert controller.is_verbose
        assert not controller.is_quiet

    def test_initialization_with_console(self, mock_console):
        """Test VerbosityController initialization with custom console."""
        controller = VerbosityController(console=mock_console)
        assert controller._console is mock_console

    def test_is_quiet_property(self):
        """Test is_quiet property for quiet mode."""
        controller = VerbosityController(level=VerbosityLevel.QUIET)
        assert controller.is_quiet
        assert not controller.is_verbose

    def test_is_verbose_property(self):
        """Test is_verbose property for verbose mode."""
        controller = VerbosityController(level=VerbosityLevel.VERBOSE)
        assert controller.is_verbose
        assert not controller.is_quiet

    def test_is_debug_property(self):
        """Test is_debug property for debug mode."""
        controller = VerbosityController(level=VerbosityLevel.DEBUG)
        assert controller.is_debug
        assert controller.is_verbose

    def test_is_trace_property(self):
        """Test is_trace property for trace mode."""
        controller = VerbosityController(level=VerbosityLevel.TRACE)
        assert controller.is_trace
        assert controller.is_debug
        assert controller.is_verbose

    def test_should_log_error_always_shown(self):
        """Test that errors are always logged regardless of level."""
        quiet_controller = VerbosityController(level=VerbosityLevel.QUIET)
        normal_controller = VerbosityController(level=VerbosityLevel.NORMAL)
        verbose_controller = VerbosityController(level=VerbosityLevel.VERBOSE)

        assert quiet_controller.should_log("error")
        assert normal_controller.should_log("error")
        assert verbose_controller.should_log("error")

    def test_should_log_levels(self):
        """Test should_log for different verbosity levels."""
        controller = VerbosityController(level=VerbosityLevel.NORMAL)

        # Normal level should show error, quiet, normal, info
        assert controller.should_log("error")
        assert controller.should_log("normal")
        assert controller.should_log("info")

        # But not verbose, debug, trace
        assert not controller.should_log("verbose")
        assert not controller.should_log("debug")
        assert not controller.should_log("trace")

    def test_should_log_verbose(self):
        """Test should_log for verbose level."""
        controller = VerbosityController(level=VerbosityLevel.VERBOSE)

        assert controller.should_log("error")
        assert controller.should_log("normal")
        assert controller.should_log("verbose")
        assert not controller.should_log("debug")

    def test_should_show(self):
        """Test should_show method."""
        controller = VerbosityController(level=VerbosityLevel.VERBOSE)

        assert controller.should_show(VerbosityLevel.QUIET)
        assert controller.should_show(VerbosityLevel.NORMAL)
        assert controller.should_show(VerbosityLevel.VERBOSE)
        assert not controller.should_show(VerbosityLevel.DEBUG)

    def test_log_normal_message(self, mock_console):
        """Test logging normal message."""
        controller = VerbosityController(level=VerbosityLevel.NORMAL, console=mock_console)
        controller.log("Test message", level="normal")

        mock_console.print.assert_called_once_with("Test message")

    def test_log_error_message(self, mock_console):
        """Test logging error message with styling."""
        controller = VerbosityController(level=VerbosityLevel.NORMAL, console=mock_console)
        controller.log("Error occurred", level="error")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert isinstance(call_args[0][0], Text)
        assert "Error occurred" in str(call_args[0][0])

    def test_log_debug_message(self, mock_console):
        """Test logging debug message with DEBUG prefix."""
        controller = VerbosityController(level=VerbosityLevel.DEBUG, console=mock_console)
        controller.log("Debug info", level="debug")

        mock_console.print.assert_called_once_with("DEBUG: Debug info")

    def test_log_trace_message(self, mock_console):
        """Test logging trace message with TRACE prefix."""
        controller = VerbosityController(level=VerbosityLevel.TRACE, console=mock_console)
        controller.log("Trace info", level="trace")

        mock_console.print.assert_called_once_with("TRACE: Trace info")

    def test_log_suppressed_by_level(self, mock_console):
        """Test that messages below verbosity level are suppressed."""
        controller = VerbosityController(level=VerbosityLevel.NORMAL, console=mock_console)
        controller.log("Verbose message", level="verbose")

        mock_console.print.assert_not_called()

    def test_from_verbose_count(self):
        """Test creating controller from -v flag count."""
        # No -v flags = normal
        controller0 = VerbosityController.from_verbose_count(0)
        assert controller0.level == VerbosityLevel.NORMAL

        # 1 -v flag = verbose
        controller1 = VerbosityController.from_verbose_count(1)
        assert controller1.level == VerbosityLevel.VERBOSE

        # 2 -v flags = debug
        controller2 = VerbosityController.from_verbose_count(2)
        assert controller2.level == VerbosityLevel.DEBUG

        # 3+ -v flags = trace
        controller3 = VerbosityController.from_verbose_count(3)
        assert controller3.level == VerbosityLevel.TRACE

        controller4 = VerbosityController.from_verbose_count(10)
        assert controller4.level == VerbosityLevel.TRACE

    def test_from_flags_quiet(self):
        """Test creating controller from CLI flags with quiet mode."""
        controller = VerbosityController.from_flags(quiet=True)
        assert controller.level == VerbosityLevel.QUIET
        assert controller.is_quiet

    def test_from_flags_verbose_count(self):
        """Test creating controller from CLI flags with verbose count."""
        controller = VerbosityController.from_flags(quiet=False, verbose_count=2)
        assert controller.level == VerbosityLevel.DEBUG

    def test_from_flags_quiet_overrides_verbose(self):
        """Test that quiet flag overrides verbose count."""
        controller = VerbosityController.from_flags(quiet=True, verbose_count=3)
        assert controller.level == VerbosityLevel.QUIET


class TestErrorCollector:
    """Tests for ErrorCollector class."""

    def test_initialization(self):
        """Test ErrorCollector initialization."""
        collector = ErrorCollector()
        assert collector.error_count == 0
        assert not collector.has_errors
        assert len(collector.errors) == 0

    def test_add_error(self):
        """Test adding errors to collector."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "extraction", "Could not parse PDF")

        assert collector.error_count == 1
        assert collector.has_errors
        assert len(collector.errors) == 1

        error = collector.errors[0]
        assert error.file_path == "file1.pdf"
        assert error.error_type == "extraction"
        assert error.error_message == "Could not parse PDF"

    def test_add_method(self):
        """Test simplified add method."""
        collector = ErrorCollector()
        collector.add("File not found", file="doc.txt", recoverable=True)

        assert collector.error_count == 1
        error = collector.errors[0]
        assert error.file_path == "doc.txt"
        assert error.error_type == "general"
        assert error.error_message == "File not found"

    def test_add_method_no_file(self):
        """Test add method without file path."""
        collector = ErrorCollector()
        collector.add("Generic error")

        assert collector.error_count == 1
        error = collector.errors[0]
        assert error.file_path == "unknown"

    def test_get_error_categories(self):
        """Test getting error counts by category."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "extraction", "Parse error")
        collector.add_error("file2.pdf", "extraction", "Encoding error")
        collector.add_error("file3.pdf", "timeout", "Timed out")

        categories = collector.get_error_categories()
        assert categories["extraction"] == 2
        assert categories["timeout"] == 1

    def test_get_suggestions_extraction(self):
        """Test getting suggestions for extraction errors."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "extraction", "Error")

        suggestions = collector.get_suggestions()
        assert len(suggestions) > 0
        assert any("corrupted" in s.lower() for s in suggestions)

    def test_get_suggestions_ocr(self):
        """Test getting suggestions for OCR errors."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "ocr", "OCR failed")

        suggestions = collector.get_suggestions()
        assert any("resolution" in s.lower() or "scanning" in s.lower() for s in suggestions)

    def test_get_suggestions_timeout(self):
        """Test getting suggestions for timeout errors."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "timeout", "Timeout")

        suggestions = collector.get_suggestions()
        assert any("timeout" in s.lower() for s in suggestions)

    def test_get_suggestions_empty(self):
        """Test getting suggestions with no errors returns generic suggestion."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "unknown_type", "Error")

        suggestions = collector.get_suggestions()
        assert len(suggestions) > 0

    def test_get_summary(self):
        """Test getting error summary text."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "extraction", "Error 1")
        collector.add_error("file2.pdf", "timeout", "Error 2")

        summary = collector.get_summary()
        assert "2 errors" in summary
        assert "extraction" in summary
        assert "timeout" in summary

    def test_get_summary_no_errors(self):
        """Test getting summary with no errors."""
        collector = ErrorCollector()
        summary = collector.get_summary()
        assert summary == "No errors"

    def test_render_summary_no_errors(self, mock_console):
        """Test rendering summary with no errors."""
        collector = ErrorCollector()
        collector.render_summary(console=mock_console)

        # Should not print anything for empty error list
        mock_console.print.assert_not_called()

    def test_render_summary_with_errors(self, string_console):
        """Test rendering summary with errors."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "extraction", "Parse failed")
        collector.add_error("file2.pdf", "timeout", "Timed out")

        collector.render_summary(console=string_console)

        output = string_console._test_buffer.getvalue()
        assert "file1.pdf" in output
        assert "file2.pdf" in output
        assert "extraction" in output
        assert "timeout" in output

    def test_render_summary_with_suggestions(self, string_console):
        """Test rendering summary includes suggestions."""
        collector = ErrorCollector()
        collector.add_error("file1.pdf", "ocr", "OCR failed")

        collector.render_summary(console=string_console)

        output = string_console._test_buffer.getvalue()
        assert "Suggestions" in output


class TestGetConsole:
    """Tests for get_console function."""

    def test_get_console_default(self):
        """Test get_console returns Console instance."""
        console = get_console()
        assert isinstance(console, Console)

    def test_get_console_singleton(self):
        """Test get_console returns same instance (singleton)."""
        console1 = get_console()
        console2 = get_console()
        assert console1 is console2

    def test_get_console_no_color_environment(self):
        """Test get_console respects NO_COLOR environment variable."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            reset_console()
            console = get_console()
            assert console.no_color is True

    def test_get_console_no_color_parameter(self):
        """Test get_console with explicit no_color parameter."""
        reset_console()
        console = get_console(no_color=True)
        assert console.no_color is True

    def test_get_console_color_enabled(self):
        """Test get_console with colors enabled."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure NO_COLOR is not set
            if "NO_COLOR" in os.environ:
                del os.environ["NO_COLOR"]
            reset_console()
            console = get_console(no_color=False)
            assert console.no_color is False

    def test_reset_console(self):
        """Test reset_console clears singleton."""
        console1 = get_console()
        reset_console()
        console2 = get_console()
        # After reset, should get a new instance
        assert console1 is not console2


class TestErrorInfo:
    """Tests for ErrorInfo dataclass."""

    def test_error_info_creation(self):
        """Test creating ErrorInfo instance."""
        error = ErrorInfo(
            file_path="test.pdf",
            error_type="extraction",
            error_message="Failed to parse",
        )
        assert error.file_path == "test.pdf"
        assert error.error_type == "extraction"
        assert error.error_message == "Failed to parse"
