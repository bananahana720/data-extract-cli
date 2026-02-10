"""UX assertion engine for Rich component validation.

Provides assertion functions for validating Rich terminal output including
panels, progress bars, tables, and ANSI color codes.

Story 5-0: UAT Testing Framework
AC-5.0-3: UXAssertion engine validates Rich components
"""

from __future__ import annotations

import re
from typing import Sequence


class UXAssertionError(AssertionError):
    """Assertion error with UX context."""

    def __init__(self, message: str, output: str | None = None) -> None:
        """Initialize with optional output context.

        Args:
            message: Error message
            output: The terminal output that failed validation
        """
        self.output = output
        super().__init__(message)


# -----------------------------------------------------------------------------
# ANSI Escape Code Utilities
# -----------------------------------------------------------------------------

# ANSI escape sequence pattern
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Common Rich/ANSI color codes
ANSI_COLORS = {
    "black": r"\x1b\[30m",
    "red": r"\x1b\[31m",
    "green": r"\x1b\[32m",
    "yellow": r"\x1b\[33m",
    "blue": r"\x1b\[34m",
    "magenta": r"\x1b\[35m",
    "cyan": r"\x1b\[36m",
    "white": r"\x1b\[37m",
    "bright_red": r"\x1b\[91m",
    "bright_green": r"\x1b\[92m",
    "bright_yellow": r"\x1b\[93m",
    "bright_blue": r"\x1b\[94m",
    "bright_magenta": r"\x1b\[95m",
    "bright_cyan": r"\x1b\[96m",
    "bold": r"\x1b\[1m",
    "dim": r"\x1b\[2m",
    "reset": r"\x1b\[0m",
}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        str: Text with ANSI codes removed
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)


def has_ansi_code(text: str, color: str) -> bool:
    """Check if text contains a specific ANSI color code.

    Args:
        text: Text to check
        color: Color name (e.g., "green", "red", "bold")

    Returns:
        bool: True if color code found
    """
    pattern = ANSI_COLORS.get(color.lower())
    if pattern:
        return bool(re.search(pattern, text))
    # Fallback: search for color name in markup (e.g., [green])
    return f"[{color}" in text.lower()


# -----------------------------------------------------------------------------
# Panel Assertions
# -----------------------------------------------------------------------------

# Rich panel border characters (box drawing)
PANEL_BORDER_CHARS = r"[╭╮╰╯│─┌┐└┘┃━]"


def assert_panel_displayed(output: str, title: str | None = None) -> None:
    """Assert that a Rich panel is displayed in the output.

    Detects Rich panels by looking for box drawing characters and
    optionally validates the panel title.

    Args:
        output: Terminal output to check
        title: Expected panel title (optional)

    Raises:
        UXAssertionError: If panel not found or title mismatch
    """
    clean_output = strip_ansi(output)

    # Check for panel border characters
    if not re.search(PANEL_BORDER_CHARS, clean_output):
        raise UXAssertionError(
            "No Rich panel found in output (no box drawing characters)",
            output,
        )

    if title:
        # Rich panels format titles like: ╭─ Title ─╮ or similar
        # Also check for title without box chars
        title_pattern = rf"[╭┌─━].*{re.escape(title)}.*[╮┐─━]|{re.escape(title)}"
        if not re.search(title_pattern, clean_output, re.IGNORECASE):
            raise UXAssertionError(
                f"Panel title '{title}' not found in output",
                output,
            )


def assert_panel_has_content(output: str, content: str) -> None:
    """Assert that a panel contains specific content.

    Args:
        output: Terminal output to check
        content: Expected content within panel

    Raises:
        UXAssertionError: If content not found
    """
    clean_output = strip_ansi(output)

    if content.lower() not in clean_output.lower():
        raise UXAssertionError(
            f"Expected content '{content}' not found in panel",
            output,
        )


# -----------------------------------------------------------------------------
# Progress Bar Assertions
# -----------------------------------------------------------------------------

# Progress bar characters (Unicode block elements)
PROGRESS_BAR_CHARS = r"[█▓▒░▏▎▍▌▋▊▉■□◼◻]"
# Percentage pattern
PERCENTAGE_PATTERN = r"\d{1,3}%"


def assert_progress_bar_shown(output: str) -> None:
    """Assert that a progress bar is displayed in the output.

    Detects progress bars by looking for block characters and/or
    percentage indicators.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If no progress bar found
    """
    clean_output = strip_ansi(output)

    # Check for progress bar characters
    has_bar_chars = bool(re.search(PROGRESS_BAR_CHARS, clean_output))
    # Check for percentage
    has_percentage = bool(re.search(PERCENTAGE_PATTERN, clean_output))

    if not has_bar_chars and not has_percentage:
        raise UXAssertionError(
            "No progress bar found in output (no block chars or percentage)",
            output,
        )


def assert_progress_percentage(output: str, min_percent: int = 0, max_percent: int = 100) -> None:
    """Assert that progress percentage is within expected range.

    Args:
        output: Terminal output to check
        min_percent: Minimum expected percentage
        max_percent: Maximum expected percentage

    Raises:
        UXAssertionError: If percentage out of range or not found
    """
    clean_output = strip_ansi(output)

    match = re.search(r"(\d{1,3})%", clean_output)
    if not match:
        raise UXAssertionError(
            "No percentage found in output",
            output,
        )

    percent = int(match.group(1))
    if not min_percent <= percent <= max_percent:
        raise UXAssertionError(
            f"Progress {percent}% not in expected range [{min_percent}%, {max_percent}%]",
            output,
        )


# -----------------------------------------------------------------------------
# Table Assertions
# -----------------------------------------------------------------------------


def assert_table_rendered(output: str, headers: Sequence[str] | None = None) -> None:
    """Assert that a Rich table is rendered in the output.

    Args:
        output: Terminal output to check
        headers: Expected column headers (optional)

    Raises:
        UXAssertionError: If table not found or headers mismatch
    """
    clean_output = strip_ansi(output)

    # Check for table border characters or column separators
    # Rich uses │ for column separators
    has_table_chars = bool(re.search(r"[│┃|].*[│┃|]", clean_output))

    if not has_table_chars:
        raise UXAssertionError(
            "No Rich table found in output (no column separators)",
            output,
        )

    if headers:
        for header in headers:
            if header.lower() not in clean_output.lower():
                raise UXAssertionError(
                    f"Table header '{header}' not found in output",
                    output,
                )


def assert_table_row_count(output: str, min_rows: int = 1, max_rows: int | None = None) -> None:
    """Assert that table has expected number of data rows.

    Args:
        output: Terminal output to check
        min_rows: Minimum expected rows
        max_rows: Maximum expected rows (optional)

    Raises:
        UXAssertionError: If row count out of range
    """
    clean_output = strip_ansi(output)

    # Count lines with table separators (crude but effective)
    table_lines = [line for line in clean_output.split("\n") if re.search(r"[│┃|]", line)]

    # Subtract header/border rows (typically 3-4 lines for Rich tables)
    data_rows = max(0, len(table_lines) - 4)

    if data_rows < min_rows:
        raise UXAssertionError(
            f"Table has {data_rows} rows, expected at least {min_rows}",
            output,
        )

    if max_rows is not None and data_rows > max_rows:
        raise UXAssertionError(
            f"Table has {data_rows} rows, expected at most {max_rows}",
            output,
        )


# -----------------------------------------------------------------------------
# Color Assertions
# -----------------------------------------------------------------------------


def assert_color_present(output: str, color: str) -> None:
    """Assert that a specific color is used in the output.

    Args:
        output: Terminal output to check (with ANSI codes)
        color: Color name (green, red, yellow, blue, cyan, magenta, bold, dim)

    Raises:
        UXAssertionError: If color not found
    """
    if not has_ansi_code(output, color):
        raise UXAssertionError(
            f"Color '{color}' not found in output",
            output,
        )


def assert_success_color(output: str) -> None:
    """Assert that success coloring (green) is present.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If green color not found
    """
    if not (has_ansi_code(output, "green") or has_ansi_code(output, "bright_green")):
        raise UXAssertionError(
            "Success color (green) not found in output",
            output,
        )


def assert_error_color(output: str) -> None:
    """Assert that error coloring (red) is present.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If red color not found
    """
    if not (has_ansi_code(output, "red") or has_ansi_code(output, "bright_red")):
        raise UXAssertionError(
            "Error color (red) not found in output",
            output,
        )


# -----------------------------------------------------------------------------
# Quality Distribution Assertions
# -----------------------------------------------------------------------------


def assert_quality_distribution(output: str, categories: Sequence[str] | None = None) -> None:
    """Assert that quality distribution display is present.

    Validates that quality distribution bars/metrics are shown,
    optionally checking for specific category labels.

    Args:
        output: Terminal output to check
        categories: Expected category labels (e.g., ["Excellent", "Good", "Review"])

    Raises:
        UXAssertionError: If distribution not found or categories missing
    """
    clean_output = strip_ansi(output)

    # Check for distribution indicators
    has_distribution = (
        "quality" in clean_output.lower()
        or "distribution" in clean_output.lower()
        or bool(re.search(PROGRESS_BAR_CHARS, clean_output))
        or bool(re.search(PERCENTAGE_PATTERN, clean_output))
    )

    if not has_distribution:
        raise UXAssertionError(
            "No quality distribution found in output",
            output,
        )

    if categories:
        for category in categories:
            if category.lower() not in clean_output.lower():
                raise UXAssertionError(
                    f"Quality category '{category}' not found in output",
                    output,
                )


# -----------------------------------------------------------------------------
# Error Guide Assertions
# -----------------------------------------------------------------------------


def assert_error_guide_shown(output: str) -> None:
    """Assert that an error guide/help panel is displayed.

    Validates that error output includes actionable guidance.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If error guide not found
    """
    clean_output = strip_ansi(output).lower()

    # Check for error indicators
    has_error = "error" in clean_output or "failed" in clean_output

    # Check for guidance indicators
    has_guidance = (
        "suggestion" in clean_output
        or "try" in clean_output
        or "hint" in clean_output
        or "help" in clean_output
        or "fix" in clean_output
    )

    if not has_error:
        raise UXAssertionError(
            "No error message found in output",
            output,
        )

    if not has_guidance:
        raise UXAssertionError(
            "Error shown but no guidance/suggestions provided",
            output,
        )


# -----------------------------------------------------------------------------
# Learning Mode Assertions
# -----------------------------------------------------------------------------


def assert_learning_tip(output: str) -> None:
    """Assert that a learning tip/educational content is displayed.

    Validates that output includes educational content markers.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If learning content not found
    """
    clean_output = strip_ansi(output).lower()

    # Check for learning content indicators
    learning_indicators = [
        "tip",
        "learn",
        "explained",
        "understanding",
        "step",
        "tutorial",
        "insight",
        "note:",
        "info:",
    ]

    has_learning = any(indicator in clean_output for indicator in learning_indicators)

    if not has_learning:
        raise UXAssertionError(
            "No learning tip or educational content found in output",
            output,
        )


def assert_step_indicator(output: str, step_number: int | None = None) -> None:
    """Assert that a step indicator is displayed.

    Args:
        output: Terminal output to check
        step_number: Expected step number (optional)

    Raises:
        UXAssertionError: If step indicator not found
    """
    clean_output = strip_ansi(output).lower()

    if step_number is not None:
        pattern = rf"step\s*{step_number}|{step_number}\s*[./:]"
        if not re.search(pattern, clean_output):
            raise UXAssertionError(
                f"Step {step_number} indicator not found in output",
                output,
            )
    else:
        if not re.search(r"step\s*\d+|\d+\s*[./:]", clean_output):
            raise UXAssertionError(
                "No step indicator found in output",
                output,
            )


# -----------------------------------------------------------------------------
# General Content Assertions
# -----------------------------------------------------------------------------


def assert_contains(output: str, text: str, case_sensitive: bool = False) -> None:
    """Assert that output contains specific text.

    Args:
        output: Terminal output to check
        text: Expected text
        case_sensitive: Whether to match case

    Raises:
        UXAssertionError: If text not found
    """
    clean_output = strip_ansi(output)

    if case_sensitive:
        if text not in clean_output:
            raise UXAssertionError(f"Text '{text}' not found in output", output)
    else:
        if text.lower() not in clean_output.lower():
            raise UXAssertionError(f"Text '{text}' not found in output (case-insensitive)", output)


def assert_not_contains(output: str, text: str, case_sensitive: bool = False) -> None:
    """Assert that output does not contain specific text.

    Args:
        output: Terminal output to check
        text: Text that should not appear
        case_sensitive: Whether to match case

    Raises:
        UXAssertionError: If text found
    """
    clean_output = strip_ansi(output)

    if case_sensitive:
        if text in clean_output:
            raise UXAssertionError(f"Unexpected text '{text}' found in output", output)
    else:
        if text.lower() in clean_output.lower():
            raise UXAssertionError(
                f"Unexpected text '{text}' found in output (case-insensitive)", output
            )


def assert_command_success(output: str) -> None:
    """Assert that command completed successfully.

    Checks for success indicators and absence of error indicators.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If command appears to have failed
    """
    clean_output = strip_ansi(output).lower()

    # Check for error indicators
    error_patterns = ["error:", "failed:", "exception:", "traceback"]
    for pattern in error_patterns:
        if pattern in clean_output:
            raise UXAssertionError(
                f"Command failed - found '{pattern}' in output",
                output,
            )


def assert_checkmark(output: str) -> None:
    """Assert that a checkmark/success indicator is present.

    Args:
        output: Terminal output to check

    Raises:
        UXAssertionError: If no checkmark found
    """
    clean_output = strip_ansi(output)

    checkmarks = ["✓", "✔", "[x]", "[X]", "PASS", "OK", "SUCCESS"]
    if not any(check in clean_output for check in checkmarks):
        raise UXAssertionError(
            "No checkmark or success indicator found in output",
            output,
        )
