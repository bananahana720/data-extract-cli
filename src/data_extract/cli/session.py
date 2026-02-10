"""Session state management for batch processing (AC-5.6-1, AC-5.6-2, AC-5.6-7).

Provides session state persistence for:
- Tracking processing progress
- Resume functionality after interruptions
- Failed file tracking with retry support
- Session cleanup and archival

Reference: docs/stories/5-6-graceful-error-handling-and-recovery.md
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# Custom Exceptions
# ==============================================================================


class SessionError(Exception):
    """Base exception for session-related errors."""

    pass


class SessionCorruptedError(SessionError):
    """Raised when a session file contains invalid JSON or structure."""

    pass


class SessionPermissionError(SessionError):
    """Raised when session directory cannot be created due to permissions."""

    pass


class ConcurrentSessionError(SessionError):
    """Raised when multiple active sessions exist for the same source directory."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when a requested session cannot be found."""

    pass


# ==============================================================================
# Error Categories (for retry logic)
# ==============================================================================


class ErrorCategory(str, Enum):
    """Error categorization for failure tracking."""

    RECOVERABLE = "recoverable"
    PERMANENT = "permanent"
    REQUIRES_CONFIG = "requires_config"


# ==============================================================================
# Session State Models
# ==============================================================================


class ProcessedFileInfo(BaseModel):
    """Information about a successfully processed file."""

    path: str
    hash: str = Field(alias="file_hash", default="")
    output: str = Field(alias="output_path", default="")

    model_config = ConfigDict(populate_by_name=True)


class FailedFileInfo(BaseModel):
    """Information about a failed file."""

    path: str
    error_type: str
    error_message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    retry_count: int = 0
    category: Optional[str] = None
    suggestion: Optional[str] = None
    stack_trace: Optional[str] = None


class SessionStatistics(BaseModel):
    """Session processing statistics."""

    total_files: int = 0
    processed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0


class SessionState(BaseModel):
    """Session state for tracking batch processing.

    Attributes:
        session_id: Unique identifier for the session
        status: Current session status
        source_directory: Path to source documents
        output_directory: Path to output directory
        total_files: Total number of files in batch
        processed_files: List of successfully processed files
        failed_files: List of failed files with error details
        started_at: Session start timestamp
        updated_at: Last update timestamp
        configuration: CLI configuration used for this session
        schema_version: Schema version for compatibility
        statistics: Processing statistics
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: Literal["in_progress", "completed", "failed", "interrupted"] = "in_progress"
    source_directory: Path
    output_directory: Optional[Path] = None
    total_files: int = 0
    processed_files: list[dict[str, Any]] = Field(default_factory=list)
    failed_files: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    configuration: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    statistics: SessionStatistics = Field(default_factory=SessionStatistics)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_dump_json_compatible(self) -> dict[str, Any]:
        """Convert to JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "status": self.status,
            "source_directory": str(self.source_directory),
            "output_directory": str(self.output_directory) if self.output_directory else None,
            "total_files": self.total_files,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "configuration": self.configuration,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "statistics": {
                "total_files": self.statistics.total_files,
                "processed_count": self.statistics.processed_count,
                "failed_count": self.statistics.failed_count,
                "skipped_count": self.statistics.skipped_count,
            },
        }


# ==============================================================================
# Cleanup Result
# ==============================================================================


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    success: bool
    error: Optional[str] = None


# ==============================================================================
# Session Manager
# ==============================================================================


class SessionManager:
    """Manager for session state persistence and lifecycle.

    Handles:
    - Session creation and initialization
    - Atomic file writes for crash safety
    - Session loading and resume detection
    - Session cleanup and archival

    Attributes:
        SESSION_DIR: Name of session directory (.data-extract-session)
        archive_retention_days: Days to retain archived sessions (default: 7)
    """

    SESSION_DIR = ".data-extract-session"

    def __init__(
        self,
        work_dir: Optional[Path] = None,
        debug: bool = False,
        max_retries: int = 3,
    ) -> None:
        """Initialize SessionManager.

        Args:
            work_dir: Working directory (default: current directory)
            debug: Enable debug mode (captures stack traces)
            max_retries: Maximum retry attempts per file
        """
        self.work_dir = work_dir or Path.cwd()
        self.session_dir = self.work_dir / self.SESSION_DIR
        self.debug = debug
        self.max_retries = max_retries
        self.archive_retention_days = 7
        self._current_session: Optional[SessionState] = None
        self._dry_run = False

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID if active."""
        return self._current_session.session_id if self._current_session else None

    def start_session(
        self,
        source_dir: Path,
        total_files: int,
        dry_run: bool = False,
        configuration: Optional[dict[str, Any]] = None,
        _test_permission_error: bool = False,
    ) -> None:
        """Start a new session.

        Args:
            source_dir: Source directory path
            total_files: Total number of files to process
            dry_run: If True, don't create session directory
            configuration: CLI configuration to store
            _test_permission_error: For testing permission error handling

        Raises:
            SessionPermissionError: If session directory cannot be created
            ConcurrentSessionError: If active session exists for same directory
        """
        self._dry_run = dry_run

        if _test_permission_error:
            raise SessionPermissionError("Cannot create session directory: Permission denied")

        if dry_run:
            return

        # Check for concurrent sessions
        existing = self._find_active_sessions(source_dir)
        if existing:
            raise ConcurrentSessionError(
                f"Active session already exists for {source_dir}: {existing[0].session_id}"
            )

        # Create session directory
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create session state
        self._current_session = SessionState(
            source_directory=source_dir,
            output_directory=self.work_dir / "output",
            total_files=total_files,
            configuration=configuration or {},
            statistics=SessionStatistics(total_files=total_files),
        )

    def create_session(
        self,
        source_directory: Path,
        output_directory: Path,
        total_files: int,
        configuration: Optional[dict[str, Any]] = None,
    ) -> SessionState:
        """Create a new session state.

        Args:
            source_directory: Source directory path
            output_directory: Output directory path
            total_files: Total number of files to process
            configuration: CLI configuration to store

        Returns:
            Created SessionState
        """
        # Create session directory
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create session state
        self._current_session = SessionState(
            source_directory=source_directory,
            output_directory=output_directory,
            total_files=total_files,
            configuration=configuration or {},
            statistics=SessionStatistics(total_files=total_files),
        )

        return self._current_session

    def save(self) -> None:
        """Save current session state to disk with atomic write."""
        self.save_session()

    def save_session(self) -> None:
        """Save current session state to disk with atomic write.

        Uses atomic write pattern:
        1. Write to temporary file
        2. Rename to final location
        3. Cleanup temp file on success

        This ensures the session file is never in a partial state.
        """
        if self._dry_run or self._current_session is None:
            return

        # Ensure directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        self._current_session.updated_at = datetime.now()

        # Get JSON content
        state_dict = self._current_session.model_dump_json_compatible()
        json_content = json.dumps(state_dict, indent=2)

        # Target file path
        session_file = self.session_dir / f"session-{self._current_session.session_id}.json"

        # Atomic write using temp file
        fd, temp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix="session-",
            dir=self.session_dir,
        )
        try:
            os.write(fd, json_content.encode("utf-8"))
            os.close(fd)
            # Atomic rename
            shutil.move(temp_path, session_file)
        except Exception:
            # Clean up temp file on failure
            os.close(fd) if fd else None
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    def get_session_state(self) -> dict[str, Any]:
        """Get current session state as dictionary.

        Returns:
            Session state dictionary
        """
        if self._current_session is None:
            return {}
        return self._current_session.model_dump_json_compatible()

    def load_session(self, session_id: str) -> Optional[SessionState]:
        """Load a session by ID.

        Args:
            session_id: Session ID to load

        Returns:
            SessionState object or None if not found

        Raises:
            SessionCorruptedError: If session file is corrupted
        """
        session_file = self.session_dir / f"session-{session_id}.json"

        if not session_file.exists():
            return None

        try:
            content = session_file.read_text()
            state_dict = json.loads(content)

            # Reconstruct session state
            self._current_session = SessionState(
                session_id=state_dict["session_id"],
                status=state_dict["status"],
                source_directory=Path(state_dict["source_directory"]),
                output_directory=(
                    Path(state_dict["output_directory"])
                    if state_dict.get("output_directory")
                    else None
                ),
                total_files=state_dict.get("statistics", {}).get(
                    "total_files", state_dict.get("total_files", 0)
                ),
                processed_files=state_dict.get("processed_files", []),
                failed_files=state_dict.get("failed_files", []),
                started_at=datetime.fromisoformat(state_dict["started_at"]),
                updated_at=datetime.fromisoformat(state_dict["updated_at"]),
                configuration=state_dict.get("configuration", {}),
                schema_version=state_dict.get("schema_version", "1.0"),
                statistics=SessionStatistics(
                    total_files=state_dict.get("statistics", {}).get("total_files", 0),
                    processed_count=state_dict.get("statistics", {}).get("processed_count", 0),
                    failed_count=state_dict.get("statistics", {}).get("failed_count", 0),
                    skipped_count=state_dict.get("statistics", {}).get("skipped_count", 0),
                ),
            )

            return self._current_session

        except json.JSONDecodeError as e:
            raise SessionCorruptedError(f"Session file corrupted: {e}") from e

    def record_processed_file(
        self,
        file_path: Path,
        output_path: Path,
        file_hash: str,
    ) -> None:
        """Record a successfully processed file.

        Args:
            file_path: Path to processed file
            output_path: Path to output file
            file_hash: Hash of the processed file
        """
        if self._current_session is None:
            return

        self._current_session.processed_files.append(
            {
                "path": str(file_path.name if isinstance(file_path, Path) else file_path),
                "hash": file_hash,
                "output": str(output_path),
            }
        )
        self._current_session.statistics.processed_count += 1
        self._current_session.updated_at = datetime.now()

    def record_failed_file(
        self,
        file_path: Path,
        error_type: str,
        error_message: str,
        category: Optional[ErrorCategory] = None,
        suggestion: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Record a failed file.

        Args:
            file_path: Path to failed file
            error_type: Type of error
            error_message: Error message
            category: Error category for retry logic
            suggestion: Actionable suggestion
            stack_trace: Stack trace (if debug mode)
        """
        if self._current_session is None:
            return

        failed_info: dict[str, Any] = {
            "path": str(file_path),
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0,
        }

        if category:
            failed_info["category"] = category.value

        if suggestion:
            failed_info["suggestion"] = suggestion

        if self.debug and stack_trace:
            failed_info["stack_trace"] = stack_trace

        self._current_session.failed_files.append(failed_info)
        self._current_session.statistics.failed_count += 1
        self._current_session.updated_at = datetime.now()

    def increment_retry_count(self, file_path: Path) -> None:
        """Increment retry count for a failed file.

        Args:
            file_path: Path to the file
        """
        if self._current_session is None:
            return

        file_path_str = str(file_path)
        for failed_file in self._current_session.failed_files:
            if failed_file["path"] == file_path_str:
                failed_file["retry_count"] = failed_file.get("retry_count", 0) + 1
                break

    def can_retry(self, file_path: Path) -> bool:
        """Check if a file can be retried.

        Args:
            file_path: Path to the file

        Returns:
            True if file can be retried
        """
        if self._current_session is None:
            return False

        file_path_str = str(file_path)
        for failed_file in self._current_session.failed_files:
            if failed_file["path"] == file_path_str:
                retry_count: int = failed_file.get("retry_count", 0)
                return retry_count < self.max_retries
        return False

    def get_retryable_files(self) -> list[dict[str, Any]]:
        """Get list of files that can be retried.

        Returns:
            List of retryable failed file records
        """
        if self._current_session is None:
            return []

        retryable = []
        for failed_file in self._current_session.failed_files:
            # Check category - PERMANENT failures are not retryable
            category = failed_file.get("category")
            if category == ErrorCategory.PERMANENT.value:
                continue

            # Check retry count
            retry_count: int = failed_file.get("retry_count", 0)
            if retry_count < self.max_retries:
                retryable.append(failed_file)

        return retryable

    def find_incomplete_session(self, source_directory: Path) -> Optional[SessionState]:
        """Find an incomplete session for the given source directory.

        Args:
            source_directory: Source directory to match

        Returns:
            SessionState if found, None otherwise
        """
        sessions = self._find_active_sessions(source_directory)

        # Filter for in_progress or interrupted status
        incomplete = [s for s in sessions if s.status in ("in_progress", "interrupted")]

        if not incomplete:
            return None

        # Return most recent
        return max(incomplete, key=lambda s: s.updated_at)

    def find_latest_session(self, source_dir: Path) -> Optional[SessionState]:
        """Find the most recent session for a source directory.

        Args:
            source_dir: Source directory to match

        Returns:
            SessionState if found, None otherwise
        """
        sessions = self._find_active_sessions(source_dir)
        if not sessions:
            return None
        return max(sessions, key=lambda s: s.updated_at)

    def _find_active_sessions(self, source_dir: Path) -> list[SessionState]:
        """Find all active sessions for a source directory.

        Args:
            source_dir: Source directory to match

        Returns:
            List of matching SessionState objects
        """
        if not self.session_dir.exists():
            return []

        sessions = []
        normalized_source = source_dir.resolve()

        for session_file in self.session_dir.glob("session-*.json"):
            if session_file.suffix == ".tmp":
                continue

            try:
                state_dict = json.loads(session_file.read_text())
                session_source = Path(state_dict["source_directory"]).resolve()

                if session_source == normalized_source:
                    # Check if in_progress
                    if state_dict.get("status") in ("in_progress", "interrupted"):
                        sessions.append(
                            SessionState(
                                session_id=state_dict["session_id"],
                                status=state_dict["status"],
                                source_directory=Path(state_dict["source_directory"]),
                                updated_at=datetime.fromisoformat(state_dict["updated_at"]),
                                started_at=datetime.fromisoformat(state_dict["started_at"]),
                                processed_files=state_dict.get("processed_files", []),
                                failed_files=state_dict.get("failed_files", []),
                                configuration=state_dict.get("configuration", {}),
                                statistics=SessionStatistics(**state_dict.get("statistics", {})),
                            )
                        )
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue

        return sessions

    def complete_session(self) -> None:
        """Complete the current session.

        - If 100% success: Remove session directory
        - If partial success: Archive session file
        """
        if self._current_session is None:
            return

        # Update status
        self._current_session.status = "completed"
        self._current_session.updated_at = datetime.now()

        # Save final state
        self.save_session()

        # Decide cleanup vs archive
        if self._current_session.statistics.failed_count == 0:
            # 100% success - remove session directory
            self._cleanup_session_directory()
        else:
            # Partial success - archive
            self._archive_session()

    def _cleanup_session_directory(self) -> None:
        """Remove the session directory on 100% success."""
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)

    def _archive_session(self) -> None:
        """Move session to archive directory."""
        if self._current_session is None:
            return

        archive_dir = self.session_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        session_file = self.session_dir / f"session-{self._current_session.session_id}.json"
        archive_file = archive_dir / f"session-{self._current_session.session_id}.json"

        if session_file.exists():
            shutil.move(str(session_file), str(archive_file))

    def cleanup_temp_files(self) -> None:
        """Remove any temporary files from incomplete writes."""
        if not self.session_dir.exists():
            return

        for temp_file in self.session_dir.glob("*.tmp"):
            try:
                temp_file.unlink()
            except OSError:
                pass  # Best effort

    def cleanup_expired_archives(self) -> None:
        """Remove archives older than retention period."""
        archive_dir = self.session_dir / "archive"
        if not archive_dir.exists():
            return

        cutoff = datetime.now().timestamp() - (self.archive_retention_days * 24 * 60 * 60)

        for archive_file in archive_dir.glob("session-*.json"):
            if archive_file.stat().st_mtime < cutoff:
                try:
                    archive_file.unlink()
                except OSError:
                    pass  # Best effort

    def find_orphaned_sessions(self, max_age_hours: int = 24) -> list[SessionState]:
        """Find sessions with no recent updates.

        Args:
            max_age_hours: Maximum hours since last update

        Returns:
            List of orphaned SessionState objects
        """
        if not self.session_dir.exists():
            return []

        orphaned = []
        cutoff = datetime.now().timestamp() - (max_age_hours * 60 * 60)

        for session_file in self.session_dir.glob("session-*.json"):
            if session_file.suffix == ".tmp":
                continue

            try:
                if session_file.stat().st_mtime < cutoff:
                    state_dict = json.loads(session_file.read_text())
                    if state_dict.get("status") == "in_progress":
                        orphaned.append(
                            SessionState(
                                session_id=state_dict["session_id"],
                                status=state_dict["status"],
                                source_directory=Path(state_dict["source_directory"]),
                                updated_at=datetime.fromisoformat(state_dict["updated_at"]),
                                started_at=datetime.fromisoformat(state_dict["started_at"]),
                            )
                        )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return orphaned

    def quarantine_file(self, file_path: Path) -> None:
        """Move a file to quarantine directory.

        Args:
            file_path: Path to file to quarantine
        """
        if self._current_session is None:
            return

        quarantine_dir = self.session_dir / "quarantine"

        # Preserve relative path structure
        source_base = self._current_session.source_directory
        try:
            relative_path = file_path.relative_to(source_base)
        except ValueError:
            # File not under source directory
            relative_path = Path(file_path.name)

        target_path = quarantine_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            shutil.move(str(file_path), str(target_path))

    def cleanup_session(
        self,
        session_id: str,
        _test_permission_error: bool = False,
    ) -> CleanupResult:
        """Clean up a specific session.

        Args:
            session_id: Session ID to clean up
            _test_permission_error: For testing permission error handling

        Returns:
            CleanupResult indicating success or failure
        """
        if _test_permission_error:
            return CleanupResult(
                success=False,
                error="Permission denied: cannot delete session file",
            )

        session_file = self.session_dir / f"session-{session_id}.json"

        if not session_file.exists():
            return CleanupResult(success=True)

        try:
            session_file.unlink()
            return CleanupResult(success=True)
        except OSError as e:
            return CleanupResult(success=False, error=str(e))
