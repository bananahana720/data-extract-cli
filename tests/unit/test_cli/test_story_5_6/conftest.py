"""Story 5-6 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-6 error handling and recovery testing.
Supports testing of:
- Session state persistence (AC-5.6-1)
- Resume functionality (AC-5.6-2)
- Retry commands (AC-5.6-3)
- Interactive error prompts (AC-5.6-4)
- Graceful degradation (AC-5.6-5)
- Session cleanup (AC-5.6-7)
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest

# Import shared fixtures from tests/fixtures/cli_fixtures.py
from tests.fixtures.cli_fixtures import (
    document_factory,
    env_vars_fixture,
    error_corpus_fixture,
    mock_console,
    mock_home_directory,
    session_state_fixture,
    typer_cli_runner,
)

# Re-export for local use
__all__ = [
    # Shared fixtures
    "typer_cli_runner",
    "env_vars_fixture",
    "mock_home_directory",
    "mock_console",
    "document_factory",
    "error_corpus_fixture",
    "session_state_fixture",
    # Story 5-6 specific fixtures
    "session_directory_fixture",
    "interrupted_session_fixture",
    "error_action_choices",
    "error_categories",
    "mock_inquirer_prompts",
    "tty_mode_fixture",
    "concurrent_session_fixture",
    "atomic_write_test_fixture",
    "exit_code_definitions",
    "archive_directory_fixture",
]


# ==============================================================================
# Story 5-6 Specific Fixtures
# ==============================================================================


class ErrorAction(str, Enum):
    """Error handling action choices for interactive prompts."""

    CONTINUE = "continue"
    RETRY = "retry"
    SKIP = "skip"
    STOP = "stop"


class ErrorCategory(str, Enum):
    """Error categorization for failure tracking."""

    RECOVERABLE = "recoverable"
    PERMANENT = "permanent"
    REQUIRES_CONFIG = "requires_config"


@dataclass
class SessionDirectoryFixture:
    """Fixture for testing .data-extract-session/ directory operations."""

    work_dir: Path
    session_dir: Path = field(init=False)

    def __post_init__(self):
        self.session_dir = self.work_dir / ".data-extract-session"

    def create_session_dir(self) -> Path:
        """Create the session directory."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return self.session_dir

    def cleanup(self) -> None:
        """Remove session directory if it exists."""
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)

    def create_session_file(
        self,
        session_id: str,
        status: str = "in_progress",
        processed_count: int = 0,
        failed_count: int = 0,
        total_files: int = 10,
        source_directory: str = "/docs",
    ) -> Path:
        """Create a session state JSON file."""
        self.create_session_dir()
        state = {
            "schema_version": "1.0",
            "session_id": session_id,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": status,
            "source_directory": source_directory,
            "output_directory": str(self.work_dir / "output"),
            "configuration": {"format": "json", "chunk_size": 500},
            "statistics": {
                "total_files": total_files,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "skipped_count": 0,
            },
            "processed_files": [
                {"path": f"doc_{i}.pdf", "hash": f"sha256:{i:064d}", "output": f"out/doc_{i}.json"}
                for i in range(processed_count)
            ],
            "failed_files": [
                {
                    "path": f"failed_{i}.pdf",
                    "error_type": "extraction",
                    "error_message": f"Mock error {i}",
                    "timestamp": datetime.now().isoformat(),
                    "retry_count": 0,
                }
                for i in range(failed_count)
            ],
        }
        session_file = self.session_dir / f"session-{session_id}.json"
        session_file.write_text(json.dumps(state, indent=2))
        return session_file

    def create_corrupted_session_file(self, session_id: str) -> Path:
        """Create a corrupted (invalid JSON) session file for error testing."""
        self.create_session_dir()
        session_file = self.session_dir / f"session-{session_id}.json"
        session_file.write_text("{ invalid json content")
        return session_file

    def get_archive_dir(self) -> Path:
        """Get the archive subdirectory path."""
        return self.session_dir / "archive"

    def create_archive_dir(self) -> Path:
        """Create the archive directory."""
        archive = self.get_archive_dir()
        archive.mkdir(parents=True, exist_ok=True)
        return archive


@pytest.fixture
def session_directory_fixture(tmp_path: Path) -> Generator[SessionDirectoryFixture, None, None]:
    """
    Provide session directory fixture for AC-5.6-1 and AC-5.6-7 testing.

    Creates isolated .data-extract-session/ directory for testing
    session state persistence and cleanup.

    Returns:
        SessionDirectoryFixture with helper methods for session testing
    """
    import os

    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    fixture = SessionDirectoryFixture(work_dir=work_dir)

    # Set environment variable for CLI commands to find test sessions
    original_work_dir = os.environ.get("DATA_EXTRACT_WORK_DIR")
    os.environ["DATA_EXTRACT_WORK_DIR"] = str(work_dir)

    yield fixture

    # Restore original environment
    if original_work_dir is None:
        del os.environ["DATA_EXTRACT_WORK_DIR"]
    else:
        os.environ["DATA_EXTRACT_WORK_DIR"] = original_work_dir

    fixture.cleanup()


@dataclass
class InterruptedSessionFixture:
    """Fixture for testing session resume functionality."""

    session_dir_fixture: SessionDirectoryFixture
    source_dir: Path
    files: list[Path] = field(default_factory=list)

    def create_interrupted_scenario(
        self,
        total_files: int = 50,
        processed_count: int = 28,
        failed_count: int = 2,
    ) -> dict[str, Any]:
        """
        Create an interrupted session scenario for resume testing.

        Returns:
            dict with session_file, remaining_files, and session state
        """
        # Create source files
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.files = []
        for i in range(total_files):
            file_path = self.source_dir / f"doc_{i}.pdf"
            file_path.write_bytes(b"%PDF-1.4\nTest content")
            self.files.append(file_path)

        # Create session file
        session_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        session_file = self.session_dir_fixture.create_session_file(
            session_id=session_id,
            status="interrupted",
            processed_count=processed_count,
            failed_count=failed_count,
            total_files=total_files,
            source_directory=str(self.source_dir),
        )

        return {
            "session_file": session_file,
            "session_id": session_id,
            "remaining_count": total_files - processed_count - failed_count,
            "processed_count": processed_count,
            "failed_count": failed_count,
            "total_files": total_files,
            "source_dir": self.source_dir,
        }

    def create_different_source_session(self, other_source: str = "/other/docs") -> Path:
        """Create a session for a different source directory."""
        session_id = "different-source-session"
        return self.session_dir_fixture.create_session_file(
            session_id=session_id,
            status="interrupted",
            processed_count=10,
            total_files=20,
            source_directory=other_source,
        )


@pytest.fixture
def interrupted_session_fixture(
    session_directory_fixture: SessionDirectoryFixture,
    tmp_path: Path,
) -> InterruptedSessionFixture:
    """
    Provide fixture for testing --resume functionality.

    Creates realistic interrupted session scenarios for AC-5.6-2 testing.

    Returns:
        InterruptedSessionFixture with scenario creation methods
    """
    source_dir = tmp_path / "source_docs"
    return InterruptedSessionFixture(
        session_dir_fixture=session_directory_fixture,
        source_dir=source_dir,
    )


@pytest.fixture
def error_action_choices() -> list[dict[str, str]]:
    """
    Provide error action choice definitions for prompt testing.

    Returns list matching UX-spec Journey 6 error prompt options.
    """
    return [
        {"value": "skip", "name": "Skip this file and continue", "shortcut": "s"},
        {"value": "retry", "name": "Retry with different settings", "shortcut": "r"},
        {"value": "stop", "name": "Stop processing (save progress)", "shortcut": "t"},
        {"value": "cancel", "name": "Cancel all (discard progress)", "shortcut": "c"},
    ]


@pytest.fixture
def error_categories() -> dict[str, dict[str, Any]]:
    """
    Provide error categorization definitions for failure tracking.

    Returns dict matching tech-spec Section 3.4 error categories.
    """
    return {
        "file_not_found": {
            "category": ErrorCategory.PERMANENT,
            "suggestion": "Check file path exists",
            "auto_retry": False,
        },
        "permission_denied": {
            "category": ErrorCategory.RECOVERABLE,
            "suggestion": "Check file permissions",
            "auto_retry": True,
        },
        "pdf_corrupted": {
            "category": ErrorCategory.PERMANENT,
            "suggestion": "Repair PDF or exclude",
            "auto_retry": False,
        },
        "ocr_confidence_low": {
            "category": ErrorCategory.REQUIRES_CONFIG,
            "suggestion": "Try --ocr-threshold 0.85",
            "auto_retry": False,
        },
        "memory_exceeded": {
            "category": ErrorCategory.REQUIRES_CONFIG,
            "suggestion": "Try --max-pages 100",
            "auto_retry": False,
        },
        "password_protected": {
            "category": ErrorCategory.RECOVERABLE,
            "suggestion": "Provide --password",
            "auto_retry": False,
        },
        "unsupported_format": {
            "category": ErrorCategory.PERMANENT,
            "suggestion": "Convert file format",
            "auto_retry": False,
        },
        "network_timeout": {
            "category": ErrorCategory.RECOVERABLE,
            "suggestion": "Will retry automatically",
            "auto_retry": True,
        },
    }


@dataclass
class MockInquirerPrompts:
    """Mock for InquirerPy prompts in non-interactive testing."""

    responses: list[str] = field(default_factory=list)
    response_index: int = 0
    prompts_shown: list[dict[str, Any]] = field(default_factory=list)

    def mock_select(self, message: str, choices: list[dict]) -> str:
        """Mock select prompt, returning pre-configured response."""
        self.prompts_shown.append({"type": "select", "message": message, "choices": choices})
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return choices[0]["value"]  # Default to first choice

    def mock_confirm(self, message: str, default: bool = True) -> bool:
        """Mock confirm prompt."""
        self.prompts_shown.append({"type": "confirm", "message": message, "default": default})
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response.lower() in ("y", "yes", "true", "1")
        return default

    def reset(self) -> None:
        """Reset state for new test."""
        self.response_index = 0
        self.prompts_shown.clear()

    def set_responses(self, responses: list[str]) -> None:
        """Set pre-configured responses for prompts."""
        self.responses = responses
        self.response_index = 0


@pytest.fixture
def mock_inquirer_prompts() -> MockInquirerPrompts:
    """
    Provide mock InquirerPy prompts for AC-5.6-4 testing.

    Returns:
        MockInquirerPrompts with configurable responses
    """
    return MockInquirerPrompts()


@dataclass
class TTYModeFixture:
    """Fixture for testing interactive vs non-interactive modes."""

    is_tty: bool = True

    def simulate_tty(self) -> MagicMock:
        """Create a mock that simulates TTY mode."""
        mock = MagicMock()
        mock.isatty.return_value = True
        return mock

    def simulate_non_tty(self) -> MagicMock:
        """Create a mock that simulates non-TTY (piped/scripted) mode."""
        mock = MagicMock()
        mock.isatty.return_value = False
        return mock


@pytest.fixture
def tty_mode_fixture() -> TTYModeFixture:
    """
    Provide TTY mode simulation for interactive prompt testing.

    Returns:
        TTYModeFixture for testing --interactive / --non-interactive behavior
    """
    return TTYModeFixture()


@dataclass
class ConcurrentSessionFixture:
    """Fixture for testing concurrent session handling."""

    session_dir_fixture: SessionDirectoryFixture

    def create_concurrent_sessions(self, count: int = 3) -> list[Path]:
        """Create multiple concurrent session files for the same directory."""
        sessions = []
        for i in range(count):
            session_id = f"session-{i}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            session_file = self.session_dir_fixture.create_session_file(
                session_id=session_id,
                status="in_progress",
                processed_count=i * 5,
                total_files=50,
            )
            sessions.append(session_file)
        return sessions


@pytest.fixture
def concurrent_session_fixture(
    session_directory_fixture: SessionDirectoryFixture,
) -> ConcurrentSessionFixture:
    """
    Provide fixture for testing concurrent session handling.

    Returns:
        ConcurrentSessionFixture for edge case testing
    """
    return ConcurrentSessionFixture(session_dir_fixture=session_directory_fixture)


@dataclass
class AtomicWriteTestFixture:
    """Fixture for testing atomic file write operations."""

    session_dir: Path

    def simulate_crash_during_write(self, session_file: Path) -> Path:
        """
        Simulate a crash during session file write.

        Creates a partial/temporary file that would exist if crash occurred mid-write.
        """
        temp_file = session_file.with_suffix(".tmp")
        temp_file.write_text('{"partial": true, "status":')  # Incomplete JSON
        return temp_file

    def has_temp_files(self) -> bool:
        """Check if any temp files exist (indicating incomplete writes)."""
        if not self.session_dir.exists():
            return False
        return any(f.suffix == ".tmp" for f in self.session_dir.iterdir())


@pytest.fixture
def atomic_write_test_fixture(tmp_path: Path) -> AtomicWriteTestFixture:
    """
    Provide fixture for testing atomic write operations.

    Returns:
        AtomicWriteTestFixture for crash recovery testing
    """
    session_dir = tmp_path / ".data-extract-session"
    session_dir.mkdir(parents=True, exist_ok=True)
    return AtomicWriteTestFixture(session_dir=session_dir)


@pytest.fixture
def exit_code_definitions() -> dict[int, str]:
    """
    Provide exit code definitions for batch processing.

    Returns dict matching tech-spec exit codes:
    - 0: All files processed successfully
    - 1: Partial success (some files failed)
    - 2: Complete failure (no files processed)
    - 3: Configuration error
    """
    return {
        0: "all_success",
        1: "partial_success",
        2: "complete_failure",
        3: "configuration_error",
    }


@dataclass
class ArchiveDirectoryFixture:
    """Fixture for testing session archive functionality."""

    session_dir_fixture: SessionDirectoryFixture

    def create_archived_session(
        self,
        session_id: str,
        days_old: int = 3,
    ) -> Path:
        """Create an archived session file."""
        import os
        import time

        archive_dir = self.session_dir_fixture.get_archive_dir()
        archive_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "schema_version": "1.0",
            "session_id": session_id,
            "status": "completed",
            "archived_at": datetime.now().isoformat(),
        }
        archive_file = archive_dir / f"session-{session_id}.json"
        archive_file.write_text(json.dumps(state, indent=2))

        # Set the file's modification time to be older
        if days_old > 0:
            old_time = time.time() - (days_old * 24 * 60 * 60)
            os.utime(archive_file, (old_time, old_time))

        return archive_file

    def create_expired_archive(self, session_id: str) -> Path:
        """Create an archive file older than retention period (7 days)."""
        return self.create_archived_session(session_id, days_old=10)


@pytest.fixture
def archive_directory_fixture(
    session_directory_fixture: SessionDirectoryFixture,
) -> ArchiveDirectoryFixture:
    """
    Provide fixture for testing session archive functionality.

    Returns:
        ArchiveDirectoryFixture for AC-5.6-7 testing
    """
    return ArchiveDirectoryFixture(session_dir_fixture=session_directory_fixture)


# ==============================================================================
# Pytest Markers for Story 5-6
# ==============================================================================


def pytest_configure(config):
    """Register custom markers for Story 5-6 tests."""
    config.addinivalue_line(
        "markers",
        "story_5_6: marks tests as Story 5-6 (Graceful Error Handling and Recovery)",
    )
    config.addinivalue_line(
        "markers",
        "session_state: marks tests for session state persistence (AC-5.6-1)",
    )
    config.addinivalue_line(
        "markers",
        "resume: marks tests for --resume functionality (AC-5.6-2)",
    )
    config.addinivalue_line(
        "markers",
        "retry: marks tests for retry --last command (AC-5.6-3)",
    )
    config.addinivalue_line(
        "markers",
        "error_prompts: marks tests for interactive error prompts (AC-5.6-4)",
    )
    config.addinivalue_line(
        "markers",
        "graceful_degradation: marks tests for continue-on-error (AC-5.6-5)",
    )
    config.addinivalue_line(
        "markers",
        "session_cleanup: marks tests for session cleanup (AC-5.6-7)",
    )
