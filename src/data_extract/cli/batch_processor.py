"""Batch processing with graceful error handling (AC-5.6-5).

Provides per-file error handling with continue-on-error pattern:
- Individual file try/except wrapping
- Error aggregation for summary reporting
- Graceful degradation when files fail
- Integration with session state for failure tracking

Reference: docs/tech-spec-epic-5.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from data_extract.cli.session import SessionManager

# ==============================================================================
# Result Models
# ==============================================================================


@dataclass(frozen=True)
class FileProcessingResult:
    """Result of processing a single file.

    Attributes:
        file_path: Path to the file that was processed
        success: Whether processing succeeded
        error: Error message if processing failed
        error_type: Category of error (extraction, normalization, etc.)
        output_path: Path to output file if successful
    """

    file_path: Path
    success: bool
    error: Optional[str] = None
    error_type: Optional[str] = None
    output_path: Optional[Path] = None


@dataclass(frozen=True)
class BatchProcessingResult:
    """Result of batch processing operation.

    Attributes:
        total_files: Total number of files attempted
        successful_files: List of successfully processed file paths
        failed_files: List of failed file paths with error details
        skipped_files: List of skipped file paths
    """

    total_files: int
    successful_files: list[Path]
    failed_files: list[tuple[Path, str, str]]  # (path, error_type, error_message)
    skipped_files: list[Path]

    @property
    def success_count(self) -> int:
        """Number of successfully processed files."""
        return len(self.successful_files)

    @property
    def failed_count(self) -> int:
        """Number of failed files."""
        return len(self.failed_files)

    @property
    def skipped_count(self) -> int:
        """Number of skipped files."""
        return len(self.skipped_files)


# ==============================================================================
# Batch Processor
# ==============================================================================


class BatchProcessor:
    """Batch file processor with graceful error handling.

    Implements continue-on-error pattern where individual file failures
    don't crash the entire batch. Errors are collected and reported
    at the end of processing.

    Attributes:
        work_dir: Working directory for session state
        continue_on_error: Whether to continue processing after file failures
        session_manager: Optional session manager for state tracking
    """

    def __init__(
        self,
        work_dir: Path,
        continue_on_error: bool = True,
        session_manager: Optional[SessionManager] = None,
    ) -> None:
        """Initialize batch processor.

        Args:
            work_dir: Working directory for session state
            continue_on_error: Whether to continue after file failures (default: True)
            session_manager: Optional session manager for failure tracking
        """
        self.work_dir = work_dir
        self.continue_on_error = continue_on_error
        self.session_manager = session_manager

        # Track results
        self.successful_files: list[Path] = []
        self.failed_files: list[tuple[Path, str, str]] = []
        self.skipped_files: list[Path] = []

    def process_file(
        self,
        file_path: Path,
        content: Optional[str] = None,
        **kwargs: Any,
    ) -> FileProcessingResult:
        """Process a single file with error handling.

        Wraps file processing in try/except to catch and record errors
        without propagating exceptions.

        Args:
            file_path: Path to file to process
            content: Optional pre-loaded content for testing
            **kwargs: Additional processing parameters

        Returns:
            FileProcessingResult with success/error information
        """
        try:
            # Validate file exists (unless content provided)
            if content is None and not file_path.exists():
                return FileProcessingResult(
                    file_path=file_path,
                    success=False,
                    error="File not found",
                    error_type="file_not_found",
                )

            # Simulate processing (in real implementation, would call pipeline)
            # For now, just validate the content doesn't have problematic characters
            if content is not None:
                # Check for null bytes which can cause issues in normalization
                if "\x00" in content:
                    return FileProcessingResult(
                        file_path=file_path,
                        success=False,
                        error="Content contains null bytes",
                        error_type="normalization",
                    )

            # Success case
            output_path = self.work_dir / f"{file_path.stem}.json"
            return FileProcessingResult(
                file_path=file_path,
                success=True,
                output_path=output_path,
            )

        except Exception as e:
            # Catch all exceptions and convert to error result
            error_message = str(e)
            error_type = type(e).__name__

            # Record in session manager if available
            if self.session_manager:
                self.session_manager.record_failed_file(
                    file_path=file_path,
                    error_type=error_type,
                    error_message=error_message,
                )

            return FileProcessingResult(
                file_path=file_path,
                success=False,
                error=error_message,
                error_type=error_type,
            )

    def process_batch(
        self,
        files: list[Path],
        **kwargs: Any,
    ) -> BatchProcessingResult:
        """Process multiple files with continue-on-error behavior.

        Args:
            files: List of files to process
            **kwargs: Additional processing parameters

        Returns:
            BatchProcessingResult with aggregated results
        """
        # Reset tracking lists
        self.successful_files = []
        self.failed_files = []
        self.skipped_files = []

        for file_path in files:
            result = self.process_file(file_path, **kwargs)

            if result.success:
                self.successful_files.append(file_path)
            else:
                error_type = result.error_type or "unknown"
                error_message = result.error or "Unknown error"
                self.failed_files.append((file_path, error_type, error_message))

                # If not continuing on error, stop here
                if not self.continue_on_error:
                    break

        return BatchProcessingResult(
            total_files=len(files),
            successful_files=self.successful_files,
            failed_files=self.failed_files,
            skipped_files=self.skipped_files,
        )

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of errors for reporting.

        Returns:
            Dictionary with error statistics and categorization
        """
        # Group errors by type
        errors_by_type: dict[str, list[Path]] = {}
        for file_path, error_type, _ in self.failed_files:
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(file_path)

        return {
            "total_errors": len(self.failed_files),
            "errors_by_type": {
                error_type: len(files) for error_type, files in errors_by_type.items()
            },
            "failed_files": [
                {
                    "path": str(path),
                    "error_type": error_type,
                    "error_message": error_message,
                }
                for path, error_type, error_message in self.failed_files
            ],
        }
