"""Retry logic for failed file processing (AC-5.6-3).

Provides failure categorization and retry functionality:
- FailureCategory enum (RECOVERABLE, PERMANENT, REQUIRES_CONFIG)
- record_failure function for tracking failures
- get_retryable_files function for retry command support

Reference: docs/tech-spec-epic-5.md
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from data_extract.cli.session import SessionState


# ==============================================================================
# Failure Category Enum
# ==============================================================================


class FailureCategory(str, Enum):
    """Error categorization for failure tracking and retry logic.

    Categories determine retry behavior:
    - RECOVERABLE: Auto-retry on subsequent runs (transient errors)
    - PERMANENT: Never auto-retry (file is corrupted/invalid)
    - REQUIRES_CONFIG: Retry with modified configuration
    """

    RECOVERABLE = "recoverable"
    PERMANENT = "permanent"
    REQUIRES_CONFIG = "requires_config"


# ==============================================================================
# Error Category Mapping
# ==============================================================================


ERROR_CATEGORY_MAP: dict[str, FailureCategory] = {
    # Permanent errors - file issues that won't fix themselves
    "pdf_corrupted": FailureCategory.PERMANENT,
    "file_not_found": FailureCategory.PERMANENT,
    "unsupported_format": FailureCategory.PERMANENT,
    # Recoverable errors - transient issues
    "network_timeout": FailureCategory.RECOVERABLE,
    "permission_denied": FailureCategory.RECOVERABLE,
    "resource_busy": FailureCategory.RECOVERABLE,
    # Configuration-dependent errors
    "ocr_confidence_low": FailureCategory.REQUIRES_CONFIG,
    "memory_exceeded": FailureCategory.REQUIRES_CONFIG,
    "password_protected": FailureCategory.REQUIRES_CONFIG,
}


# ==============================================================================
# Retry Functions
# ==============================================================================


def record_failure(
    session: "SessionState",
    file: Path,
    error: Exception,
    category: FailureCategory,
) -> None:
    """Record a file processing failure in the session state.

    Args:
        session: SessionState to update
        file: Path to the failed file
        error: Exception that caused the failure
        category: Failure category for retry logic
    """
    # Determine error type from exception
    error_type = _classify_error_type(error)

    # Build failure record
    failure_record: dict[str, Any] = {
        "path": str(file),
        "error_type": error_type,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat(),
        "retry_count": 0,
        "category": category.value,
    }

    # Add suggestion if available
    suggestion = _get_suggestion_for_category(category, error_type)
    if suggestion:
        failure_record["suggestion"] = suggestion

    # Append to session failed files
    session.failed_files.append(failure_record)
    session.statistics.failed_count += 1


def get_retryable_files(session: "SessionState") -> list[Path]:
    """Get list of files that can be retried.

    Files with PERMANENT category are excluded.
    Files that have exceeded max retries are excluded.

    Args:
        session: SessionState to check

    Returns:
        List of Path objects for retryable files
    """
    retryable = []

    for failed_file in session.failed_files:
        # Skip permanent failures
        category = failed_file.get("category")
        if category == FailureCategory.PERMANENT.value:
            continue

        # Get file path
        file_path = Path(failed_file["path"])
        retryable.append(file_path)

    return retryable


def categorize_error(error: Exception) -> FailureCategory:
    """Categorize an error for retry logic.

    Args:
        error: Exception to categorize

    Returns:
        FailureCategory for the error
    """
    error_type = _classify_error_type(error)
    return ERROR_CATEGORY_MAP.get(error_type, FailureCategory.RECOVERABLE)


def _classify_error_type(error: Exception) -> str:
    """Classify an error into a type string.

    Args:
        error: Exception to classify

    Returns:
        Error type string
    """
    error_str = str(error).lower()
    error_class = type(error).__name__.lower()

    if "corrupt" in error_str or "invalid" in error_str:
        return "pdf_corrupted"
    if "permission" in error_str or "access denied" in error_str:
        return "permission_denied"
    if "not found" in error_str or "no such file" in error_str:
        return "file_not_found"
    if "memory" in error_str or "out of memory" in error_str:
        return "memory_exceeded"
    if "password" in error_str or "encrypted" in error_str:
        return "password_protected"
    if "timeout" in error_str or "timed out" in error_str:
        return "network_timeout"
    if "confidence" in error_str and "ocr" in error_str:
        return "ocr_confidence_low"
    if "unsupported" in error_str or "unknown format" in error_str:
        return "unsupported_format"
    if "filenotfound" in error_class:
        return "file_not_found"
    if "permission" in error_class:
        return "permission_denied"

    return "extraction"


def _get_suggestion_for_category(
    category: FailureCategory,
    error_type: str,
) -> str:
    """Get actionable suggestion based on category and error type.

    Args:
        category: Failure category
        error_type: Error type string

    Returns:
        Suggestion string
    """
    suggestions = {
        "pdf_corrupted": "Repair PDF using tools like qpdf or pdftk, or exclude this file",
        "file_not_found": "Check that the file path exists and is accessible",
        "permission_denied": "Check file permissions or run with elevated privileges",
        "ocr_confidence_low": "Try --ocr-threshold 0.85",
        "memory_exceeded": "Try --max-pages 100",
        "password_protected": "Provide --password <password>",
        "unsupported_format": "Convert file to a supported format",
        "network_timeout": "Will retry automatically on next run",
    }

    return suggestions.get(error_type, "Check file and try again")


def should_auto_retry(category: FailureCategory) -> bool:
    """Check if a failure category should auto-retry.

    Args:
        category: Failure category

    Returns:
        True if should auto-retry
    """
    return category == FailureCategory.RECOVERABLE


def get_retry_delay(retry_count: int, base_delay: float = 1.0) -> float:
    """Calculate exponential backoff delay for retry.

    Args:
        retry_count: Current retry count (0-based)
        base_delay: Base delay in seconds

    Returns:
        Delay in seconds
    """
    # Exponential backoff with cap at 60 seconds
    delay = base_delay * (2**retry_count)
    return float(min(delay, 60.0))
