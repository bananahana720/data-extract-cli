"""Exit code standards for batch processing (AC-5.6-5).

Standardized exit codes for CLI batch processing:
- EXIT_SUCCESS (0): All files processed successfully
- EXIT_PARTIAL (1): Partial success (some files failed)
- EXIT_FAILURE (2): Complete failure (no files processed)
- EXIT_CONFIG_ERROR (3): Configuration error

Reference: docs/stories/5-6-graceful-error-handling-and-recovery.md
"""

from __future__ import annotations

# Exit code constants
EXIT_SUCCESS: int = 0
EXIT_PARTIAL: int = 1
EXIT_FAILURE: int = 2
EXIT_CONFIG_ERROR: int = 3


def determine_exit_code(
    total_files: int,
    processed_count: int,
    failed_count: int,
    config_error: bool = False,
) -> int:
    """Determine the appropriate exit code based on processing results.

    Args:
        total_files: Total number of files in the batch
        processed_count: Number of files successfully processed
        failed_count: Number of files that failed processing
        config_error: Whether a configuration error occurred

    Returns:
        Exit code integer:
        - 0: All files processed successfully
        - 1: Partial success (some files failed)
        - 2: Complete failure (no files processed)
        - 3: Configuration error

    Examples:
        >>> determine_exit_code(10, 10, 0)
        0
        >>> determine_exit_code(10, 5, 5)
        1
        >>> determine_exit_code(10, 0, 10)
        2
        >>> determine_exit_code(10, 0, 0, config_error=True)
        3
    """
    # Configuration errors take precedence
    if config_error:
        return EXIT_CONFIG_ERROR

    # Empty batch is considered success (nothing to fail)
    if total_files == 0:
        return EXIT_SUCCESS

    # All files succeeded
    if failed_count == 0 and processed_count > 0:
        return EXIT_SUCCESS

    # Some files succeeded, some failed (partial success)
    if processed_count > 0 and failed_count > 0:
        return EXIT_PARTIAL

    # Complete failure (no files processed successfully)
    if processed_count == 0:
        return EXIT_FAILURE

    # Default to partial if there's any ambiguity
    return EXIT_PARTIAL
