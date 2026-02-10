"""Feedback components for CLI output and verbosity control.

This module provides:
- VerbosityController: Controls output levels based on -q/-v/-vv/-vvv flags
- VerbosityLevel: Enum for verbosity levels (QUIET, NORMAL, VERBOSE, DEBUG, TRACE)
- ErrorCollector: Accumulates errors during batch processing
- get_console: Factory for Rich Console respecting NO_COLOR environment variable
- reset_console: Reset singleton console for testing

AC-5.3-5: NO_COLOR environment variable support
AC-5.3-8: Quiet mode (-q) and verbose levels (-v, -vv, -vvv)
AC-5.3-9: Continue-on-error pattern with ErrorCollector
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from data_extract.cli.ocr_status import get_ocr_unavailable_suggestion


class VerbosityLevel(IntEnum):
    """Verbosity levels for CLI output control.

    Maps to CLI flags:
    - QUIET (0): -q/--quiet - only errors
    - NORMAL (1): default - summary and key metrics
    - VERBOSE (2): -v - detailed per-file info
    - DEBUG (3): -vv - full trace and timing
    - TRACE (4): -vvv - maximum detail
    """

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3
    TRACE = 4


class VerbosityController:
    """Controls output verbosity based on CLI flags.

    Usage:
        controller = VerbosityController(level=2)  # verbose
        if controller.should_log("verbose"):
            controller.log("Processing file.pdf", level="verbose")
    """

    # Map level names to VerbosityLevel values
    LEVEL_MAP = {
        "error": VerbosityLevel.QUIET,  # Always shown
        "quiet": VerbosityLevel.QUIET,
        "normal": VerbosityLevel.NORMAL,
        "info": VerbosityLevel.NORMAL,
        "verbose": VerbosityLevel.VERBOSE,
        "debug": VerbosityLevel.DEBUG,
        "trace": VerbosityLevel.TRACE,
    }

    def __init__(
        self,
        level: int = VerbosityLevel.NORMAL,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize VerbosityController.

        Args:
            level: Verbosity level (0-4). Defaults to 1 (NORMAL).
            console: Rich Console for output. If None, uses get_console().
        """
        self._level = level
        self._console = console or get_console()

    @property
    def level(self) -> int:
        """Current verbosity level."""
        return self._level

    @property
    def is_quiet(self) -> bool:
        """True if in quiet mode (level 0)."""
        return self._level == VerbosityLevel.QUIET

    @property
    def is_verbose(self) -> bool:
        """True if verbose or higher (level >= 2)."""
        return self._level >= VerbosityLevel.VERBOSE

    @property
    def is_debug(self) -> bool:
        """True if debug or higher (level >= 3)."""
        return self._level >= VerbosityLevel.DEBUG

    @property
    def is_trace(self) -> bool:
        """True if trace mode (level >= 4)."""
        return self._level >= VerbosityLevel.TRACE

    def should_log(self, level: str) -> bool:
        """Check if message at given level should be logged.

        Args:
            level: One of "error", "quiet", "normal", "info", "verbose", "debug", "trace"

        Returns:
            True if message should be logged at current verbosity
        """
        required_level = self.LEVEL_MAP.get(level.lower(), VerbosityLevel.NORMAL)
        # Errors are always shown
        if level.lower() == "error":
            return True
        return self._level >= required_level

    def should_show(self, required_level: VerbosityLevel) -> bool:
        """Check if content requiring given level should be shown.

        Args:
            required_level: Minimum verbosity level required

        Returns:
            True if current level is sufficient
        """
        return self._level >= required_level

    def log(self, message: str, level: str = "normal", **kwargs: Any) -> None:
        """Log a message if current verbosity allows it.

        Args:
            message: Message to log
            level: Verbosity level required for this message
            **kwargs: Additional arguments passed to console.print()
        """
        if not self.should_log(level):
            return

        # Format based on level
        if level.lower() == "error":
            text = Text(message, style="bold red")
            self._console.print(text, **kwargs)
        elif level.lower() == "debug":
            self._console.print(f"DEBUG: {message}", **kwargs)
        elif level.lower() == "trace":
            self._console.print(f"TRACE: {message}", **kwargs)
        else:
            self._console.print(message, **kwargs)

    @classmethod
    def from_verbose_count(
        cls, count: int, console: Optional[Console] = None
    ) -> "VerbosityController":
        """Create controller from -v flag count.

        Args:
            count: Number of -v flags (0 to 3+)
            console: Optional console instance

        Returns:
            VerbosityController with appropriate level
        """
        # 0 -v flags = normal (1)
        # 1 -v flag = verbose (2)
        # 2 -v flags = debug (3)
        # 3+ -v flags = trace (4)
        level = min(VerbosityLevel.NORMAL + count, VerbosityLevel.TRACE)
        return cls(level=level, console=console)

    @classmethod
    def from_flags(
        cls,
        quiet: bool = False,
        verbose_count: int = 0,
        console: Optional[Console] = None,
    ) -> "VerbosityController":
        """Create controller from CLI flags.

        Args:
            quiet: True if -q/--quiet flag was used
            verbose_count: Number of -v flags (0-3)
            console: Optional console instance

        Returns:
            VerbosityController with appropriate level
        """
        if quiet:
            return cls(level=VerbosityLevel.QUIET, console=console)
        return cls.from_verbose_count(verbose_count, console=console)


@dataclass
class ErrorInfo:
    """Information about a single error during processing."""

    file_path: str
    error_type: str
    error_message: str


class ErrorCollector:
    """Collects errors during batch processing for continue-on-error pattern.

    Allows processing to continue after individual file errors while
    accumulating error information for summary display.

    Usage:
        collector = ErrorCollector()
        try:
            process_file(f)
        except Exception as e:
            collector.add_error(f.name, "extraction", str(e))
        collector.render_summary(console)
    """

    # Suggestion templates by error type
    SUGGESTIONS = {
        "ocr": [
            "Consider re-scanning documents at higher resolution",
            "Ensure OCR language settings match document content",
        ],
        "ocr_unavailable": None,  # Dynamically generated
        "scanned_pdf_no_ocr": None,  # Dynamically generated
        "timeout": [
            "Try increasing the timeout with --timeout option",
            "Consider splitting large documents into smaller chunks",
        ],
        "extraction": [
            "Check if the file is corrupted or password-protected",
            "Try converting the document to a different format first",
        ],
        "validation": [
            "Verify the file format matches its extension",
            "Ensure the file was not truncated during transfer",
        ],
    }

    def __init__(self) -> None:
        """Initialize empty error collector."""
        self._errors: list[ErrorInfo] = []

    @property
    def errors(self) -> list[ErrorInfo]:
        """List of collected errors."""
        return self._errors

    @property
    def error_count(self) -> int:
        """Number of errors collected."""
        return len(self._errors)

    @property
    def has_errors(self) -> bool:
        """True if any errors have been collected."""
        return len(self._errors) > 0

    def add(
        self,
        error: str,
        file: Optional[str] = None,
        recoverable: bool = True,
    ) -> None:
        """Add an error with simplified interface.

        Args:
            error: Error message
            file: Optional file path
            recoverable: Whether the error is recoverable (ignored, for API compatibility)
        """
        self._errors.append(
            ErrorInfo(
                file_path=file or "unknown",
                error_type="general",
                error_message=error,
            )
        )

    def add_error(
        self,
        file_path: str,
        error_type: str,
        error_message: str,
    ) -> None:
        """Add an error to the collection.

        Args:
            file_path: Path to the file that caused the error
            error_type: Category of error (extraction, validation, timeout, ocr)
            error_message: Detailed error message
        """
        self._errors.append(
            ErrorInfo(
                file_path=file_path,
                error_type=error_type,
                error_message=error_message,
            )
        )

    def get_error_categories(self) -> dict[str, int]:
        """Get error counts grouped by type.

        Returns:
            Dict mapping error type to count
        """
        categories: dict[str, int] = {}
        for error in self._errors:
            categories[error.error_type] = categories.get(error.error_type, 0) + 1
        return categories

    def get_suggestions(self) -> list[str]:
        """Get actionable suggestions based on error types.

        Returns:
            List of suggestion strings
        """
        suggestions: list[str] = []
        seen_types: set[str] = set()

        for error in self._errors:
            if error.error_type not in seen_types:
                seen_types.add(error.error_type)

                # Handle dynamic OCR suggestions
                if error.error_type in ("ocr_unavailable", "scanned_pdf_no_ocr"):
                    suggestions.append(get_ocr_unavailable_suggestion())
                else:
                    type_suggestions = self.SUGGESTIONS.get(error.error_type, [])
                    if type_suggestions:
                        suggestions.extend(type_suggestions)

        # Add generic suggestion if no specific ones
        if not suggestions and self._errors:
            suggestions.append(
                "Review failed files and check for common issues (corruption, encoding)"
            )

        return suggestions

    def get_summary(self) -> str:
        """Get text summary of errors.

        Returns:
            Summary string with error count and categories
        """
        if not self._errors:
            return "No errors"

        categories = self.get_error_categories()
        parts = [f"{count} {error_type}" for error_type, count in categories.items()]
        return f"{self.error_count} errors: {', '.join(parts)}"

    def render_summary(self, console: Optional[Console] = None) -> None:
        """Render error summary to console.

        Args:
            console: Rich Console instance. Uses get_console() if None.
        """
        console = console or get_console()

        if not self._errors:
            # No output for empty error list (or minimal success message)
            return

        # Create error table
        table = Table(title="Errors Summary", show_header=True, header_style="bold red")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Message", style="white")

        for error in self._errors:
            table.add_row(error.file_path, error.error_type, error.error_message)

        # Create panel with table and suggestions
        suggestions = self.get_suggestions()
        suggestion_text = "\n".join(f"  - {s}" for s in suggestions) if suggestions else ""

        if suggestion_text:
            console.print(table)
            console.print(
                Panel(
                    suggestion_text,
                    title="Suggestions",
                    border_style="yellow",
                )
            )
        else:
            console.print(table)


# Global console singleton
_console: Optional[Console] = None


def reset_console() -> None:
    """Reset the global console singleton.

    Used primarily for testing to ensure clean state between tests.
    """
    global _console
    _console = None


def get_console(no_color: Optional[bool] = None) -> Console:
    """Get Rich Console instance respecting NO_COLOR environment.

    Implements singleton pattern with NO_COLOR detection for accessibility.
    The NO_COLOR standard (https://no-color.org/) disables colored output.

    Args:
        no_color: Override for NO_COLOR detection. If None, checks environment.

    Returns:
        Configured Rich Console instance
    """
    global _console

    # Determine no_color setting
    if no_color is None:
        # Per NO_COLOR spec, presence of the variable (any value including empty) disables colors
        # However, common convention treats empty string as "not set"
        # We follow the stricter interpretation: any non-empty value disables colors
        # Empty string also disables per spec: "When set (to any value, including empty string)"
        no_color = "NO_COLOR" in os.environ

    # Return singleton if settings match
    if _console is not None and _console.no_color == no_color:
        return _console

    # Create new console with appropriate settings
    _console = Console(
        no_color=no_color,
        force_terminal=not no_color,
        legacy_windows=False,
    )

    return _console


__all__ = [
    "VerbosityLevel",
    "VerbosityController",
    "ErrorCollector",
    "ErrorInfo",
    "get_console",
    "reset_console",
]
